import logging
import threading
from datetime import datetime, timedelta, timezone as dt_timezone
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache
from tasks.models import Task
from tasks.services.calendar import (
    adjust_to_working_hours,
    get_working_intervals,
    is_working_day,
    to_org_tz,
)

logger = logging.getLogger(__name__)

# Thread-local storage to track scheduler execution depth and prevent infinite recursion on task save commit hooks
_thread_locals = threading.local()

# ==============================================================================
# Algorithm v2: Advanced Task Scheduling Algorithm
# ==============================================================================
# 1. Get current time -> timezone.now() (Safely handles real-time start)
# 2. Load Organization Settings (working hours, breaks, max scan days = 7)
# 3. Load User's existing tasks (filter by assigned user + scheduled tasks, excluding completed tasks)
# 4. Find the last task end time of this user (this creates perfect task chaining)
#    - If no last task, or last task end time is in the past, starting point is current time.
# 5. From that starting point, scan forward up to max_scan_days (default 7) working days:
#    - Skip weekends and holidays (leaves)
#    - Respect daily breaks (Lunch 1-2pm, Tea 5-5:30pm)
#    - Find the earliest single continuous slot that fits the full estimated hours
# 6. If slot found -> Save/Return scheduled_start_date/time and scheduled_end_date/time
# 7. If no slot found in scan period -> Return None, None (Put task in Queue Bucket with status "Waiting For Capacity")
# ==============================================================================

class SchedulerService:
    @classmethod
    def is_running(cls):
        """Checks if the scheduler is currently executing to bypass signal-triggered reschedules."""
        return getattr(_thread_locals, 'scheduler_depth', 0) > 0

    @classmethod
    def increment_depth(cls):
        """Increments reentrant depth of scheduler execution."""
        _thread_locals.scheduler_depth = getattr(_thread_locals, 'scheduler_depth', 0) + 1

    @classmethod
    def decrement_depth(cls):
        """Decrements reentrant depth of scheduler execution."""
        _thread_locals.scheduler_depth = max(0, getattr(_thread_locals, 'scheduler_depth', 0) - 1)

    @staticmethod
    def _estimated_minutes(estimated_hours: float) -> int:
        if not estimated_hours:
            estimated_hours = 1.0
        return max(1, int(round(float(estimated_hours) * 60)))

    @staticmethod
    def _serialize_segments(segments):
        """
        Store segmented schedules in the same JSON shape used by the scheduler.
        Keeping this in one place prevents Task Details, Task List, and preview
        responses from drifting after a manual duration/start edit.
        """
        import json
        return json.dumps([
            {
                "start": seg["start"].isoformat(),
                "end": seg["end"].isoformat(),
                "duration": seg["duration"],
            }
            for seg in segments
        ])

    @staticmethod
    def _logical_workday(dt, org, user=None):
        """
        Return the schedule day that owns dt. Overnight shifts that end after
        midnight still belong to the previous workday.
        """
        schedule = None
        if user:
            from users.models import UserWorkingSchedule
            schedule = UserWorkingSchedule.objects.filter(user=user).first()

        work_start = getattr(schedule, 'work_start_time', None) or org.working_start_time
        work_end = getattr(schedule, 'work_end_time', None) or org.working_end_time

        logical_day = dt.date()
        if work_end < work_start and dt.time() <= work_end:
            logical_day -= timedelta(days=1)
        return logical_day

    @classmethod
    def _build_segments_from_anchor(cls, task, start_time, duration_minutes):
        """
        Build the exact working-time segments for one task from a requested
        start. The start is snapped only when it falls outside the assignee's
        working intervals, so valid manual starts are preserved.
        """
        org = task.organization
        assignee = task.assignee
        duration_minutes = max(1, int(duration_minutes or task.total_estimated_minutes))

        local_start = to_org_tz(start_time, org).replace(second=0, microsecond=0)
        leave_dates = cls._get_leave_dates(task.assignee_id, local_start, org)
        cursor = adjust_to_working_hours(local_start, org, leave_dates=leave_dates, user=assignee)
        cursor = cursor.replace(second=0, microsecond=0)

        max_working_days = getattr(org, 'maximum_scan_days', 7) or 7
        remaining = duration_minutes
        segments = []
        working_days_seen = 0
        current_day = cls._logical_workday(cursor, org, assignee)
        calendar_days_checked = 0

        while remaining > 0 and working_days_seen < max_working_days and calendar_days_checked < 60:
            calendar_days_checked += 1

            if not is_working_day(current_day, org, leave_dates):
                current_day += timedelta(days=1)
                continue

            working_days_seen += 1
            intervals = get_working_intervals(current_day, org, user=assignee)

            for interval_start, interval_end in intervals:
                if interval_end <= cursor:
                    continue

                active_start = max(interval_start, cursor)
                if active_start >= interval_end:
                    continue

                available = int(round((interval_end - active_start).total_seconds() / 60.0))
                allocated = min(available, remaining)
                active_end = active_start + timedelta(minutes=allocated)

                segments.append({
                    "start": active_start.astimezone(dt_timezone.utc),
                    "end": active_end.astimezone(dt_timezone.utc),
                    "duration": allocated,
                })

                remaining -= allocated
                cursor = active_end

                if remaining <= 0:
                    return segments

            current_day += timedelta(days=1)

        return None

    @staticmethod
    def _get_leave_dates(assignee_id, start_time, organization):
        cache_key = f"assignee_leaves_{assignee_id}_{to_org_tz(start_time, organization).date().isoformat()}"
        leave_dates = cache.get(cache_key)
        if leave_dates is not None:
            return leave_dates

        leave_dates = set()
        from users.models import LeaveRequest

        leaves = LeaveRequest.objects.filter(
            user_id=assignee_id,
            status='Approved',
            end_date__gte=to_org_tz(start_time, organization).date(),
        ).only('start_date', 'end_date')

        for leave in leaves:
            current = leave.start_date
            while current <= leave.end_date:
                leave_dates.add(current)
                current += timedelta(days=1)

        cache.set(cache_key, leave_dates, 10)  # Cache leaves for 10 seconds
        return leave_dates

    @staticmethod
    def _subtract_intervals(working_intervals, occupied_intervals):
        """
        Subtracts occupied intervals from working intervals.
        Both lists contain tuples of (start_datetime, end_datetime) in the same timezone.
        """
        occupied = sorted(occupied_intervals, key=lambda x: x[0])
        free_intervals = []
        for w_start, w_end in working_intervals:
            current_start = w_start
            for o_start, o_end in occupied:
                if o_end <= current_start:
                    continue
                if o_start >= w_end:
                    break
                if o_start > current_start:
                    free_intervals.append((current_start, o_start))
                current_start = max(current_start, o_end)
                if current_start >= w_end:
                    break
            if current_start < w_end:
                free_intervals.append((current_start, w_end))
        return free_intervals

    @staticmethod
    def _day_capacity_minutes(day, org, user=None):
        return sum(
            int(round((end - start).total_seconds() / 60.0))
            for start, end in get_working_intervals(day, org, user=user)
        )

    @classmethod
    def _build_free_segments(
        cls,
        candidate_start,
        duration_minutes,
        allowed_workdays,
        org,
        user,
        occupied_intervals,
    ):
        """
        Build a task window from a free candidate start.

        Breaks are pausable working-calendar gaps, so a task may resume after
        lunch/tea. Existing tasks are hard blockers: if the required duration
        would cross one, this candidate is rejected and the caller tries the
        next real free gap.
        """
        allowed = set(allowed_workdays)
        day_order = {day: idx for idx, day in enumerate(allowed_workdays)}
        current_day = cls._logical_workday(candidate_start, org, user)
        remaining = max(1, int(duration_minutes))
        cursor = candidate_start
        segments = []

        # Short tasks should not consume a tiny end-of-day remainder and spill
        # into tomorrow; long tasks that cannot fit in any single day may span.
        day_capacity = cls._day_capacity_minutes(current_day, org, user=user)
        must_finish_same_day = remaining <= day_capacity
        start_day = current_day

        while current_day in allowed and remaining > 0:
            if must_finish_same_day and current_day != start_day:
                return None

            intervals = get_working_intervals(current_day, org, user=user)
            for interval_start, interval_end in intervals:
                if interval_end <= cursor:
                    continue

                active_start = max(interval_start, cursor)
                if active_start >= interval_end:
                    continue

                blocker_start = None
                for busy_start, busy_end in occupied_intervals:
                    if busy_end <= active_start:
                        continue
                    if busy_start >= interval_end:
                        break
                    if busy_start <= active_start < busy_end:
                        return None
                    blocker_start = busy_start
                    break

                usable_end = min(interval_end, blocker_start) if blocker_start else interval_end
                if usable_end <= active_start:
                    return None

                available = int(round((usable_end - active_start).total_seconds() / 60.0))
                allocated = min(available, remaining)
                active_end = active_start + timedelta(minutes=allocated)
                segments.append({
                    "start": active_start,
                    "end": active_end,
                    "duration": allocated,
                })
                remaining -= allocated
                cursor = active_end

                if remaining <= 0:
                    return segments
                if blocker_start and cursor >= blocker_start:
                    return None

            next_index = day_order.get(current_day, -1) + 1
            if next_index >= len(allowed_workdays):
                break
            current_day = allowed_workdays[next_index]
            next_intervals = get_working_intervals(current_day, org, user=user)
            if not next_intervals:
                continue
            cursor = next_intervals[0][0]

        return None

    @classmethod
    def _get_busy_slots(cls, assignee_id, range_start_utc, range_end_utc, exclude_task_ids=None):
        """
        Retrieves all occupied time intervals for the assignee.
        Excludes completed/done tasks and respects any task that has planned start/end times.

        exclude_task_ids: list of UUIDs to exclude, or the string "ALL" to exclude
        all tasks (used when recalculating a task's end time in isolation).
        """
        # Special case: "ALL" means treat the schedule as completely empty
        # (used by TaskDetailView when recalculating a single task's slot)
        if exclude_task_ids == "ALL":
            return []

        tasks = Task.objects.filter(
            assignee_id=assignee_id,
            planned_start__isnull=False,
            planned_end__isnull=False,
            is_deleted=False,
            planned_start__lt=range_end_utc,
            planned_end__gt=range_start_utc
        ).exclude(status='done')
        
        if exclude_task_ids:
            if not isinstance(exclude_task_ids, (list, set, tuple)):
                exclude_task_ids = [exclude_task_ids]
            tasks = tasks.exclude(id__in=exclude_task_ids)
            
        tasks = tasks.only('planned_start', 'planned_end')
        
        return [(task.planned_start, task.planned_end) for task in tasks]

    @classmethod
    def get_last_task_end_time(cls, assignee_id, org, now_dt=None):
        """
        Finds the latest end time of all scheduled tasks of this user.
        If no tasks scheduled or last task end time is in the past, returns current time.
        """
        if now_dt is None:
            now_dt = timezone.now()
            
        last_task = Task.objects.filter(
            assignee_id=assignee_id,
            planned_start__isnull=False,
            planned_end__isnull=False,
            is_deleted=False
        ).exclude(status='done').order_by('-planned_end').first()
        
        if last_task:
            return max(now_dt, last_task.planned_end)
        return now_dt

    @classmethod
    def find_earliest_slot(cls, assignee_id, duration_minutes: int, org, start_search_from: datetime, is_preview: bool = False, user=None, exclude_task_ids=None, additional_occupied=None):
        """
        From start_search_from, scans forward up to 7 working days:
        - Skip weekends and holidays (leaves)
        - Respect daily breaks (Lunch 1-2pm, Tea 5-5:30pm)
        - Find the earliest single continuous slot that fits the full duration in minutes.
        Returns one segment in organization's local timezone, or None when no
        continuous gap in the scan window can hold the whole task.
        """
        start_search_from = to_org_tz(start_search_from, org).replace(second=0, microsecond=0)
        required_minutes = duration_minutes
        leave_dates = cls._get_leave_dates(assignee_id, start_search_from, org)
        
        try:
            import zoneinfo
            tz = zoneinfo.ZoneInfo(org.timezone)
        except Exception:
            tz = timezone.get_current_timezone()

        schedule = None
        if user:
            from users.models import UserWorkingSchedule
            schedule = UserWorkingSchedule.objects.filter(user=user).first()

        user_w_start = getattr(schedule, 'work_start_time', None) or org.working_start_time
        user_w_end = getattr(schedule, 'work_end_time', None) or org.working_end_time

        # Step 1: Identify the next working days from the requested search
        # anchor. Callers that want "right now" already pass timezone.now();
        # callers that are reflowing from an existing same-day task end must
        # not be pushed to tomorrow just because the wall clock has moved past
        # today's shift.
        max_scan_days = getattr(org, 'maximum_scan_days', 7)
        if not max_scan_days:
            max_scan_days = 7

        allowed_workdays = []
        current_date = start_search_from.date()
        is_overnight = user_w_end < user_w_start
        
        if is_overnight and start_search_from.time() <= user_w_end:
            # The early-morning portion of an overnight shift belongs to the
            # previous logical workday.
            current_date -= timedelta(days=1)
            
        # If the anchor is already past the selected logical day's shift end,
        # then and only then advance to the next day.
        shift_start = datetime.combine(current_date, user_w_start, tzinfo=tz)
        shift_end = datetime.combine(current_date, user_w_end, tzinfo=tz)
        if is_overnight:
            shift_end += timedelta(days=1)
            
        if start_search_from >= shift_end:
            current_date += timedelta(days=1)

        # A partially-used current day should not consume one of the "next 7
        # working days" we promise to scan. We still check the remaining time
        # today first, then scan seven full working days after it before
        # queueing. A search before work starts already has the full day
        # available, so it counts as one of the seven.
        includes_partial_anchor_day = shift_start < start_search_from < shift_end
        days_to_scan = max_scan_days + (1 if includes_partial_anchor_day else 0)
            
        calendar_days_checked = 0
        while len(allowed_workdays) < days_to_scan and calendar_days_checked < 90:
            if is_working_day(current_date, org, leave_dates):
                allowed_workdays.append(current_date)
            current_date += timedelta(days=1)
            calendar_days_checked += 1

        logger.info(
            f"[Scheduler] Scanning up to {len(allowed_workdays)} working days for assignee {assignee_id}. "
            f"Allowed days: {[d.strftime('%Y-%m-%d') for d in allowed_workdays]}"
        )

        if not allowed_workdays:
            logger.warning("[Scheduler] No working days found in the next 30 calendar days.")
            return None

        # Determine range for querying occupied intervals: cover all allowed workdays
        range_start = start_search_from
        range_end = datetime.combine(allowed_workdays[-1] + timedelta(days=1), user_w_start, tzinfo=tz)
        
        range_start_utc = range_start.astimezone(dt_timezone.utc)
        range_end_utc = range_end.astimezone(dt_timezone.utc)

        # Retrieve occupied intervals (no caching to ensure real-time accuracy)
        occupied_intervals = cls._get_busy_slots(assignee_id, range_start_utc, range_end_utc, exclude_task_ids=exclude_task_ids)
        if additional_occupied:
            occupied_intervals.extend(additional_occupied)

        # Convert occupied intervals to organization local timezone
        org_occupied = []
        for t_start, t_end in occupied_intervals:
            org_occupied.append((to_org_tz(t_start, org), to_org_tz(t_end, org)))
        org_occupied.sort(key=lambda x: x[0])

        start_time_perf = datetime.now()

        # Step 2: Try to find a slot within the allowed working days
        for day_idx, day in enumerate(allowed_workdays):
            if (datetime.now() - start_time_perf).total_seconds() > 3.0:
                logger.warning("[Scheduler] Scanning timed out during slot search.")
                return None

            logger.debug(f"[Scheduler] Checking day {day.strftime('%Y-%m-%d')} (Working day {day_idx + 1}/{len(allowed_workdays)})")

            # Get working intervals for this day
            working_intervals = get_working_intervals(day, org, user=user)
            free_intervals = cls._subtract_intervals(working_intervals, org_occupied)

            # Find a candidate start time on this day. Breaks may be crossed by
            # pausing/resuming, but occupied task intervals may not be crossed.
            for start, end in free_intervals:
                if end <= start_search_from:
                    continue
                candidate_start = max(start, start_search_from)
                if candidate_start >= end:
                    continue

                segments = cls._build_free_segments(
                    candidate_start=candidate_start,
                    duration_minutes=required_minutes,
                    allowed_workdays=allowed_workdays[day_idx:],
                    org=org,
                    user=user,
                    occupied_intervals=org_occupied,
                )

                if segments:
                    logger.info(
                        f"[Scheduler] Continuous slot found. "
                        f"Scanned {day_idx + 1} working days."
                    )
                    return segments

        logger.info(
            f"[Scheduler] Insufficient capacity within {len(allowed_workdays)} working days for assignee {assignee_id}. "
            f"Task will be queued."
        )
        return None

    @classmethod
    def get_next_available_slot(cls, assignee_id, duration_minutes: int, org_id, start_search_from: datetime = None, is_preview: bool = False, user=None, exclude_task_ids=None, additional_occupied=None):
        """
        Finds the next available working slot for one assignee.
        Delegates to find_earliest_slot.
        """
        if is_preview:
            return cls._get_next_available_slot_impl(assignee_id, duration_minutes, org_id, start_search_from, is_preview, user, exclude_task_ids, additional_occupied)
        else:
            with transaction.atomic():
                return cls._get_next_available_slot_impl(assignee_id, duration_minutes, org_id, start_search_from, is_preview, user, exclude_task_ids, additional_occupied)

    @classmethod
    def _get_next_available_slot_impl(cls, assignee_id, duration_minutes: int, org_id, start_search_from: datetime = None, is_preview: bool = False, user=None, exclude_task_ids=None, additional_occupied=None):
        if not assignee_id or not org_id:
            return None

        if not user and assignee_id:
            from django.contrib.auth import get_user_model
            try:
                user = get_user_model().objects.get(id=assignee_id)
            except Exception:
                pass

        from organizations.models import Organization
        try:
            org = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return None

        # 1. Get current time -> timezone.now()
        now_dt = timezone.now()

        # Start search from current time to allow intelligent gap filling
        if not start_search_from:
            start_search_from = now_dt

        # 5. From that starting point, scan forward up to 7 working days
        segments_local = cls.find_earliest_slot(
            assignee_id=assignee_id,
            duration_minutes=duration_minutes,
            org=org,
            start_search_from=start_search_from,
            is_preview=is_preview,
            user=user,
            exclude_task_ids=exclude_task_ids,
            additional_occupied=additional_occupied
        )

        if segments_local:
            # Return in UTC as expected by DB fields and other components
            utc_segments = []
            for seg in segments_local:
                utc_segments.append({
                    "start": seg["start"].astimezone(dt_timezone.utc),
                    "end": seg["end"].astimezone(dt_timezone.utc),
                    "duration": seg["duration"]
                })
            return utc_segments

        return None

    @classmethod
    def recalculate_task_window(cls, task, start_time=None, duration_minutes=None):
        """
        Recalculate one task from an anchored start and exact working duration.

        This is intentionally different from normal scheduling: when a user edits
        Scheduled Start or Estimated Hours in Task Details, the backend must keep
        that task anchored and only recompute Scheduled End using the assignee's
        working calendar, lunch, tea break, holidays/leaves, and overnight shifts.
        Other tasks are handled afterward by cascade_reschedule_tasks().
        """
        if not task.assignee_id or not task.organization_id:
            return None

        anchored_start = start_time or task.planned_start or timezone.now()
        duration = duration_minutes or task.total_estimated_minutes

        segments = cls._build_segments_from_anchor(task, anchored_start, duration)
        if not segments:
            return None

        return {
            "planned_start": segments[0]["start"],
            "planned_end": segments[-1]["end"],
            "schedule_reason": cls._serialize_segments(segments),
            "segments": segments,
        }

    @classmethod
    def _new_task_search_anchor(cls, task, assignee_user, fallback_start=None):
        """
        Pick the search anchor for a newly-created task.

        Normal scheduling starts at the current wall-clock time. One important
        exception prevents premature next-day jumps: if the wall clock is
        already past today's shift end, but today's planned schedule still has
        unused capacity after the last task, start from that last task's end so
        the current workday is filled before tomorrow is considered.
        """
        if fallback_start:
            return fallback_start

        now_dt = timezone.now()
        org = task.organization
        local_now = to_org_tz(now_dt, org).replace(second=0, microsecond=0)

        try:
            import zoneinfo
            tz = zoneinfo.ZoneInfo(org.timezone)
        except Exception:
            tz = timezone.get_current_timezone()

        schedule = None
        if assignee_user:
            from users.models import UserWorkingSchedule
            schedule = UserWorkingSchedule.objects.filter(user=assignee_user).first()

        work_start = getattr(schedule, 'work_start_time', None) or org.working_start_time
        work_end = getattr(schedule, 'work_end_time', None) or org.working_end_time
        is_overnight = work_end < work_start

        logical_day = local_now.date()
        if is_overnight and local_now.time() <= work_end:
            logical_day -= timedelta(days=1)

        shift_start = datetime.combine(logical_day, work_start, tzinfo=tz)
        shift_end = datetime.combine(logical_day, work_end, tzinfo=tz)
        if is_overnight:
            shift_end += timedelta(days=1)

        if local_now < shift_end:
            return now_dt

        last_today_task = (
            Task.objects.filter(
                assignee_id=task.assignee_id,
                organization_id=task.organization_id,
                planned_start__isnull=False,
                planned_end__isnull=False,
                planned_start__lt=shift_end.astimezone(dt_timezone.utc),
                planned_end__gt=shift_start.astimezone(dt_timezone.utc),
                planned_end__lt=shift_end.astimezone(dt_timezone.utc),
                is_deleted=False,
            )
            .exclude(id=task.id)
            .exclude(status='done')
            .order_by('-planned_end')
            .only('planned_end')
            .first()
        )

        if last_today_task:
            return last_today_task.planned_end

        return now_dt

    @classmethod
    @transaction.atomic
    def schedule_single_task_in_earliest_gap(cls, task, start_search_from=None):
        """
        Schedule one newly-created or queued task without moving existing tasks.

        This is the create/preview counterpart to the full timeline reflow:
        - It reads the assignee's personal working schedule.
        - It respects existing scheduled tasks, breaks, holidays, and leaves.
        - It fills real gaps first.
        - It queues the task when the 7-working-day window has no capacity.
        """
        if not task.assignee_id or not task.organization_id:
            task.planned_start = None
            task.planned_end = None
            task.schedule_status = 'QUEUED'
            task.queue_position = None
            task.schedule_reason = "No assignee"
            task.last_scheduler_run = timezone.now()
            task.save(update_fields=[
                'planned_start', 'planned_end', 'schedule_status',
                'updated_at', 'queue_position', 'schedule_reason',
                'last_scheduler_run'
            ])
            return task

        cls.increment_depth()
        try:
            from django.contrib.auth import get_user_model
            try:
                assignee_user = get_user_model().objects.get(id=task.assignee_id)
            except Exception:
                assignee_user = task.assignee

            search_anchor = cls._new_task_search_anchor(task, assignee_user, start_search_from)
            segments = cls.get_next_available_slot(
                task.assignee_id,
                task.total_estimated_minutes,
                task.organization_id,
                start_search_from=search_anchor,
                user=assignee_user,
                exclude_task_ids=[task.id]
            )

            task.last_scheduler_run = timezone.now()
            task.is_auto_scheduled = True

            if segments:
                task.planned_start = segments[0]["start"]
                task.planned_end = segments[-1]["end"]
                task.schedule_status = 'SCHEDULED'
                task.queue_position = None
                task.schedule_reason = cls._serialize_segments(segments)
            else:
                task.planned_start = None
                task.planned_end = None
                task.schedule_status = 'QUEUED'
                task.queue_position = None
                task.schedule_reason = "Task will go to Queue Bucket (No available slots within the 7-day scheduling window)."

            task._skip_dynamic_reschedule = True
            task.save(update_fields=[
                'planned_start', 'planned_end', 'schedule_status',
                'updated_at', 'queue_position', 'schedule_reason',
                'last_scheduler_run', 'is_auto_scheduled'
            ])
            return task
        finally:
            cls.decrement_depth()

    @classmethod
    @transaction.atomic
    def schedule_tasks_for_assignee(cls, assignee_id, org_id, include_manual=False, from_datetime=None):
        """
        Schedules queued and future tasks for a specific assignee, packing them tightly.

        The queue crawler uses the default include_manual=False so manually
        pinned tasks are left alone. Profile, leave, and explicit reflow paths
        use include_manual=True so every future task respects changed working
        hours and breaks.
        """
        if not assignee_id or not org_id:
            return []

        cls.increment_depth()
        try:
            from django.contrib.auth import get_user_model
            from django.db.models import Q
            User = get_user_model()
            try:
                assignee_user = User.objects.get(id=assignee_id)
            except Exception:
                assignee_user = None
                
            from organizations.models import Organization
            try:
                org = Organization.objects.get(id=org_id)
            except Exception:
                org = None

            invalidate_assignee_occupied_cache(assignee_id)
            now_dt = from_datetime or timezone.now()

            # 1. Fetch all future scheduled tasks and queued tasks
            task_query = (
                Task.objects.select_for_update()
                .filter(
                    assignee_id=assignee_id,
                    organization_id=org_id,
                    is_deleted=False,
                )
                .exclude(status__in=['done', 'cancelled', 'archived'])
            )
            if not include_manual:
                task_query = task_query.filter(is_auto_scheduled=True)

            scheduled_window = Q(schedule_status='SCHEDULED', planned_start__gte=now_dt)
            if include_manual:
                scheduled_window |= Q(schedule_status='SCHEDULED', planned_end__gt=now_dt)

            tasks = list(task_query.filter(Q(schedule_status='QUEUED') | scheduled_window))

            # Store original status to detect changes
            for task in tasks:
                task._original_status_before_schedule = task.schedule_status
                task._original_planned_start = task.planned_start

            # 2. Sorting logic to preserve order
            # Scheduled tasks get primary priority based on their original planned_start
            # Queued tasks get secondary priority based on Priority > Impact > Risk > Due Date > Created Date
            priority_order = {'high': 0, 'medium': 1, 'low': 2}
            risk_order = {'high': 0, 'medium': 1, 'low': 2}
            
            def sort_key(t):
                is_scheduled = (t.schedule_status == 'SCHEDULED' and t.planned_start is not None)
                return (
                    0 if is_scheduled else 1,
                    t.planned_start.timestamp() if is_scheduled else float('inf'),
                    priority_order.get(str(t.priority).lower(), 1),
                    -(getattr(t, 'impact', 0) or 0),
                    risk_order.get(str(t.risk).lower(), 1) if hasattr(t, 'risk') else 1,
                    t.due_date.timestamp() if t.due_date else float('inf'),
                    t.created_at.timestamp() if t.created_at else float('inf')
                )

            tasks.sort(key=sort_key)

            scheduled_tasks = []
            queue_pos = 1
            additional_occupied = []
            exclude_task_ids = [t.id for t in tasks]
            
            for task in tasks:
                duration_minutes = task.total_estimated_minutes
                
                segments = cls.get_next_available_slot(
                    assignee_id, 
                    duration_minutes, 
                    org_id, 
                    start_search_from=now_dt,
                    user=assignee_user,
                    additional_occupied=additional_occupied,
                    exclude_task_ids=exclude_task_ids
                )

                task.last_scheduler_run = timezone.now()

                if segments:
                    planned_start = segments[0]["start"]
                    planned_end = segments[-1]["end"]
                    task.planned_start = planned_start
                    task.planned_end = planned_end
                    task.schedule_status = 'SCHEDULED'
                    task.queue_position = None
                    
                    task.schedule_reason = cls._serialize_segments(segments)
                    task.save(update_fields=['planned_start', 'planned_end', 'schedule_status', 'updated_at', 'queue_position', 'schedule_reason', 'last_scheduler_run'])
                    scheduled_tasks.append(task)
                    
                    for seg in segments:
                        additional_occupied.append((seg["start"], seg["end"]))
                    
                    if getattr(task, '_original_status_before_schedule', None) == 'QUEUED' and not getattr(task, '_is_rescheduling_run', False):
                        from notifications.services import NotificationService
                        NotificationService.send_notification(
                            recipient=task.assignee,
                            n_type="task_scheduled_from_queue",
                            title="Task Scheduled",
                            message=f"Your queued task '{task.title}' has been scheduled to start on {planned_start.strftime('%d %b %Y, %I:%M %p')}.",
                            link=f"/tasks/{task.id}",
                            organization=task.organization
                        )
                else:
                    task.planned_start = None
                    task.planned_end = None
                    task.schedule_status = 'QUEUED'
                    task.queue_position = queue_pos
                    task.schedule_reason = "Waiting For Capacity"
                    task.save(update_fields=['planned_start', 'planned_end', 'schedule_status', 'updated_at', 'queue_position', 'schedule_reason', 'last_scheduler_run'])
                    queue_pos += 1

            return scheduled_tasks
        finally:
            cls.decrement_depth()

    @classmethod
    @transaction.atomic
    def reschedule_assignee_tasks(cls, assignee_id, org_id):
        """
        Processes the queue for an assignee without wiping existing scheduled tasks.
        """
        if not assignee_id or not org_id:
            return []

        # We no longer wipe all auto-scheduled tasks here. 
        # This function simply triggers schedule_tasks_for_assignee which pulls 'QUEUED' tasks
        # and appends them to the existing scheduled timeline.
        return cls.schedule_tasks_for_assignee(assignee_id, org_id)

    @classmethod
    @transaction.atomic
    def cascade_reschedule_tasks(cls, user, changed_task_id, old_planned_start=None, old_planned_end=None):
        """
        Re-chain the changed task and every later task for the same assignee.

        Robust cascade rules:
        1. The changed task is authoritative. Its end is recalculated from
           planned_start + estimated duration before any later task is touched.
        2. Every task that was scheduled at/after the changed task's original
           position is removed from the busy-slot calculation as a group.
        3. Those later tasks are then rebuilt one by one from the previous
           task's new end time. This makes overlap impossible inside the chain,
           including when work crosses breaks, dates, weekends, leaves, or
           overnight schedules.
        4. Queued tasks for the same user are appended after the scheduled
           chain so they do not get stranded behind stale task times.
        """
        try:
            changed_task = Task.objects.select_for_update().get(id=changed_task_id)
        except Task.DoesNotExist:
            return

        if not changed_task.assignee_id or not changed_task.organization_id:
            return

        cls.increment_depth()
        try:
            from django.db.models import Q
            from django.contrib.auth import get_user_model

            original_start = old_planned_start or changed_task.planned_start or timezone.now()
            original_end = old_planned_end or original_start
            original_boundary = min(original_start, original_end)

            # Always make the edited task internally consistent first. Task
            # Details may send only estimated_hours or only planned_start; this
            # ensures planned_end is the result of start + working duration.
            if changed_task.planned_start:
                recalculated = cls.recalculate_task_window(
                    changed_task,
                    start_time=changed_task.planned_start,
                    duration_minutes=changed_task.total_estimated_minutes
                )
                if recalculated:
                    changed_task.planned_start = recalculated["planned_start"]
                    changed_task.planned_end = recalculated["planned_end"]
                    changed_task.schedule_status = 'SCHEDULED'
                    changed_task.queue_position = None
                    changed_task.schedule_reason = recalculated["schedule_reason"]
                    changed_task.last_scheduler_run = timezone.now()
                    changed_task._skip_dynamic_reschedule = True
                    changed_task.save(update_fields=[
                        'planned_start', 'planned_end', 'schedule_status',
                        'updated_at', 'queue_position', 'schedule_reason',
                        'last_scheduler_run'
                    ])

            # Fetch every task that was originally after the changed task.
            # planned_end > original_boundary also catches tasks that were
            # already overlapping the edited task's old position, so a bad
            # existing timeline is repaired instead of preserved.
            tasks = list(
                Task.objects.select_for_update()
                .filter(
                    assignee_id=changed_task.assignee_id,
                    organization_id=changed_task.organization_id,
                    is_deleted=False
                )
                .exclude(id=changed_task.id)
                .exclude(status__in=['done', 'cancelled', 'archived'])
                .filter(
                    Q(schedule_status='QUEUED') |
                    Q(schedule_status='SCHEDULED', planned_start__gte=original_boundary) |
                    Q(schedule_status='SCHEDULED', planned_end__gt=original_boundary)
                )
            )

            # Sort scheduled tasks by their original timeline, then append
            # queued tasks by business priority. This keeps sequence stable
            # while still giving unscheduled work a deterministic order.
            priority_order = {'high': 0, 'medium': 1, 'low': 2}
            risk_order = {'high': 0, 'medium': 1, 'low': 2}
            
            def sort_key(t):
                is_scheduled = (t.schedule_status == 'SCHEDULED' and t.planned_start is not None)
                return (
                    0 if is_scheduled else 1,
                    t.planned_start.timestamp() if is_scheduled else float('inf'),
                    priority_order.get(str(t.priority).lower(), 1),
                    -(getattr(t, 'impact', 0) or 0),
                    risk_order.get(str(t.risk).lower(), 1) if hasattr(t, 'risk') else 1,
                    t.due_date.timestamp() if t.due_date else float('inf'),
                    t.created_at.timestamp() if t.created_at else float('inf')
                )

            tasks.sort(key=sort_key)
            
            # Chain every following task after the changed task's new end.
            current_anchor = (
                changed_task.planned_end or
                changed_task.planned_start or
                timezone.now()
            )
                
            User = get_user_model()
            assignee_user = user if user else None
            if not assignee_user:
                try:
                    assignee_user = User.objects.get(id=changed_task.assignee_id)
                except Exception:
                    assignee_user = None

            # Exclude the whole cascade set, including the changed task, from
            # busy-slot checks. We then add each newly generated segment back
            # into additional_occupied as the chain is rebuilt.
            additional_occupied = []
            exclude_task_ids = [changed_task.id] + [t.id for t in tasks]
            queue_pos = 1
            
            for task in tasks:
                duration_minutes = task.total_estimated_minutes
                
                segments = cls.get_next_available_slot(
                    changed_task.assignee_id, 
                    duration_minutes, 
                    changed_task.organization_id, 
                    start_search_from=current_anchor,
                    user=assignee_user,
                    additional_occupied=additional_occupied,
                    exclude_task_ids=exclude_task_ids
                )
                
                task.last_scheduler_run = timezone.now()

                if segments:
                    planned_start = segments[0]["start"]
                    planned_end = segments[-1]["end"]
                    task.planned_start = planned_start
                    task.planned_end = planned_end
                    task.schedule_status = 'SCHEDULED'
                    task.queue_position = None
                    
                    task.schedule_reason = cls._serialize_segments(segments)
                    task._skip_dynamic_reschedule = True
                    task.save(update_fields=['planned_start', 'planned_end', 'schedule_status', 'updated_at', 'queue_position', 'schedule_reason', 'last_scheduler_run'])
                    
                    for seg in segments:
                        additional_occupied.append((seg["start"], seg["end"]))
                        
                    # The next task cannot start before this new end.
                    current_anchor = planned_end
                else:
                    task.planned_start = None
                    task.planned_end = None
                    task.schedule_status = 'QUEUED'
                    task.schedule_reason = "Waiting For Capacity"
                    task.queue_position = queue_pos
                    task._skip_dynamic_reschedule = True
                    task.save(update_fields=[
                        'planned_start', 'planned_end', 'schedule_status',
                        'updated_at', 'queue_position', 'schedule_reason',
                        'last_scheduler_run'
                    ])
                    queue_pos += 1

        finally:
            cls.decrement_depth()

    @classmethod
    def cascadeRescheduleTasks(cls, user, changed_task_id, old_planned_start=None, old_planned_end=None):
        """
        Backward-compatible camelCase wrapper for callers/tests that use the
        frontend naming. The implementation lives in cascade_reschedule_tasks.
        """
        return cls.cascade_reschedule_tasks(user, changed_task_id, old_planned_start, old_planned_end)

    @classmethod
    def reschedule_user_future_tasks(cls, user_id):
        """
        Finds all organizations where the user has future tasks and triggers a reschedule
        from the current time. This is used when a user updates their personal working schedule.
        """
        now = timezone.now()
        from django.db.models import Q

        org_ids = Task.objects.filter(
            assignee_id=user_id,
            is_deleted=False,
        ).filter(
            Q(schedule_status='QUEUED') |
            Q(planned_start__gte=now) |
            Q(planned_end__gt=now)
        ).exclude(status__in=['done', 'cancelled', 'archived']).values_list('organization_id', flat=True).distinct()

        for org_id in org_ids:
            cls.schedule_tasks_for_assignee(user_id, org_id, include_manual=True, from_datetime=now)

    @classmethod
    @transaction.atomic
    def reschedule_from_datetime(cls, assignee_id, org_id, from_datetime):
        """
        Triggers the intelligent reflow logic for an assignee to fill gaps and preserve order.
        Delegates to schedule_tasks_for_assignee which handles its own depth tracking.
        """
        if not assignee_id or not org_id or not from_datetime:
            return []
        # Note: schedule_tasks_for_assignee already manages increment/decrement_depth,
        # so we do NOT wrap with extra depth here to avoid double-incrementing.
        return cls.schedule_tasks_for_assignee(
            assignee_id,
            org_id,
            include_manual=True,
            from_datetime=from_datetime
        )

    @classmethod
    @transaction.atomic
    def reschedule_subsequent_tasks(cls, task_id):
        """
        Given a task ID, reschedule all subsequent tasks for the same assignee.
        Delegates to cascade_reschedule_tasks.
        """
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return
        return cls.cascade_reschedule_tasks(task.assignee, task.id)




def get_task_schedule_details(task):
    if not task.planned_start or not task.planned_end:
        return {
            "scheduled_date": None,
            "start_time": None,
            "end_time": None,
            "status": task.schedule_status,
        }

    try:
        org = task.organization
        planned_start = to_org_tz(task.planned_start, org)
        planned_end = to_org_tz(task.planned_end, org)
    except Exception:
        import zoneinfo
        tz = zoneinfo.ZoneInfo("Asia/Kolkata")
        planned_start = task.planned_start.astimezone(tz)
        planned_end = task.planned_end.astimezone(tz)
        
    return {
        "scheduled_date": planned_start.strftime("%d %b %Y"),
        "start_time": planned_start.strftime("%H:%M"),
        "end_time": planned_end.strftime("%H:%M"),
        "status": task.schedule_status,
    }


def get_next_available_slot(
    assignee_id,
    duration_minutes: int,
    org_id,
    start_search_from: datetime = None,
    is_preview: bool = False,
    user=None,
    exclude_task_id=None,
    exclude_task_ids=None,
    additional_occupied=None,
):
    """
    Backward-compatible wrapper used by preview/views.

    Older callers pass a single exclude_task_id; cascade code may pass a list.
    Normalizing both here keeps every entry point on the same scheduler logic.
    """
    excluded = exclude_task_ids if exclude_task_ids is not None else exclude_task_id
    return SchedulerService.get_next_available_slot(
        assignee_id,
        duration_minutes,
        org_id,
        start_search_from,
        is_preview,
        user,
        excluded,
        additional_occupied,
    )


@transaction.atomic
def schedule_tasks_for_assignee(assignee_id, org_id):
    return SchedulerService.schedule_tasks_for_assignee(assignee_id, org_id)


@transaction.atomic
def reschedule_assignee_tasks(assignee_id, org_id):
    return SchedulerService.reschedule_assignee_tasks(assignee_id, org_id)


@transaction.atomic
def cascade_reschedule_tasks(user, changed_task_id, old_planned_start=None, old_planned_end=None):
    return SchedulerService.cascade_reschedule_tasks(user, changed_task_id, old_planned_start, old_planned_end)


@transaction.atomic
def reschedule_subsequent_tasks(task_id):
    return SchedulerService.reschedule_subsequent_tasks(task_id)


def reschedule_from_datetime(assignee_id, org_id, from_datetime):
    """Top-level wrapper for SchedulerService.reschedule_from_datetime."""
    return SchedulerService.reschedule_from_datetime(assignee_id, org_id, from_datetime)


def invalidate_assignee_occupied_cache(assignee_id):
    if not assignee_id:
        return
    cache_key = f"assignee_cache_version_{assignee_id}"
    cache.delete(cache_key)


def get_last_task_end_time(assignee_id, org, now_dt=None):
    return SchedulerService.get_last_task_end_time(assignee_id, org, now_dt)


def find_earliest_slot(assignee_id, duration_minutes: int, org, start_search_from: datetime, is_preview: bool = False, user=None):
    return SchedulerService.find_earliest_slot(assignee_id, duration_minutes, org, start_search_from, is_preview, user)
