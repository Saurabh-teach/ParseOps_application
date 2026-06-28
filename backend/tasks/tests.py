from datetime import datetime, timedelta, time
from django.utils import timezone
from django.db.models import Q
from tasks.models import Task
from users.models import UserWorkingSchedule

class SchedulerService:
    def get_user_schedule(self, user):
        """Get user's working schedule or return default"""
        try:
            return UserWorkingSchedule.objects.filter(user=user).first() or getattr(user, 'working_schedule')
        except:
            # Default schedule
            return type('DefaultSchedule', (), {
                'work_start_time': time(10, 0),
                'lunch_start_time': time(13, 0),
                'lunch_duration_minutes': 60,
                'tea_start_time': time(17, 0),
                'tea_duration_minutes': 30,
            })()

    def calculate_task_score(self, task):
        """Simple priority-based scoring"""
        priority_map = {'High': 3, 'Medium': 2, 'Low': 1}
        return priority_map.get(task.priority, 2)

    def get_last_task_end(self, user):
        """Get the latest end time of user's scheduled tasks"""
        last_task = Task.objects.filter(
            assigned_to=user,
            scheduled_end_date__isnull=False
        ).order_by('-scheduled_end_date', '-scheduled_end_time').first()

        if last_task and last_task.scheduled_end_date and last_task.scheduled_end_time:
            return timezone.datetime.combine(
                last_task.scheduled_end_date, 
                last_task.scheduled_end_time
            )
        return None

    def schedule_task(self, task):
        """Main scheduling logic"""
        user = task.assigned_to
        if not user:
            return None

        schedule = self.get_user_schedule(user)
        now = timezone.now()
        last_end = self.get_last_task_end(user)
        start_from = max(now, last_end) if last_end else now

        current = start_from
        days_scanned = 0

        while days_scanned < 7:
            if current.weekday() >= 5:  # Skip weekend
                current += timedelta(days=1)
                current = current.replace(hour=schedule.work_start_time.hour, minute=0)
                continue

            # Try to schedule on current day
            slot = self.find_slot_on_day(current, task.estimated_minutes, schedule, user)
            if slot:
                task.scheduled_start_date = slot[0].date()
                task.scheduled_start_time = slot[0].time()
                task.scheduled_end_date = slot[1].date()
                task.scheduled_end_time = slot[1].time()
                task.save()
                return slot

            # Move to next day
            current += timedelta(days=1)
            current = current.replace(hour=schedule.work_start_time.hour, minute=0)
            days_scanned += 1

        # No slot found → Queue
        task.scheduler_status = 'queued'
        task.save()
        return None

    def find_slot_on_day(self, start_time, duration_minutes, schedule, user):
        """Find available slot on a specific day"""
        day_start = start_time.replace(hour=schedule.work_start_time.hour, minute=0)
        day_end = start_time.replace(hour=schedule.work_start_time.hour + 8, minute=0)

        current = max(start_time, day_start)

        while current + timedelta(minutes=duration_minutes) <= day_end:
            if self.is_time_in_break(current, schedule):
                current += timedelta(minutes=schedule.lunch_duration_minutes if current.hour == 13 else schedule.tea_duration_minutes)
                continue

            # Check if slot is free (no overlapping tasks)
            if not self.has_overlap(current, duration_minutes, user):
                end_time = current + timedelta(minutes=duration_minutes)
                return current, end_time

            current += timedelta(minutes=15)  # Check every 15 min

        return None

    def is_time_in_break(self, current, schedule):
        """Check if time is in lunch or tea break"""
        if current.hour == schedule.lunch_start_time.hour:
            return True
        if current.hour == schedule.tea_start_time.hour:
            return True
        return False

    def has_overlap(self, start, duration, user):
        """Check if time slot overlaps with existing tasks"""
        end = start + timedelta(minutes=duration)
        return Task.objects.filter(
            assigned_to=user,
            scheduled_start_date=start.date(),
            scheduled_end_date__gte=start.date()
        ).filter(
            Q(scheduled_start_time__lt=end.time()) &
            Q(scheduled_end_time__gt=start.time())
        ).exists()
