from datetime import datetime, time, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from organizations.models import Organization, OrganizationMembership
from tasks.models import Task
from tasks.services.calendar import to_org_tz
from tasks.services.scheduler import SchedulerService
from notifications.models import Notification
from users.models import UserWorkingSchedule
from users.serializers import UserSerializer


class SchedulerServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="assignee@example.com",
            password="password",
        )
        self.org = Organization.objects.create(
            name="Scheduler Test Org",
            owner=self.user,
            created_by=self.user,
            timezone="Asia/Kolkata",
            working_days=[0, 1, 2, 3, 4, 5, 6],
            maximum_scan_days=7,
        )
        OrganizationMembership.objects.create(
            organization=self.org,
            user=self.user,
            role="owner",
            is_active=True,
        )

    def set_user_schedule(
        self,
        work_start,
        work_end,
        lunch_start,
        lunch_end,
        tea_start,
        tea_end,
    ):
        schedule, _ = UserWorkingSchedule.objects.get_or_create(user=self.user)
        schedule.work_start_time = work_start
        schedule.work_end_time = work_end
        schedule.lunch_break_start = lunch_start
        schedule.lunch_break_end = lunch_end
        schedule.tea_break_start = tea_start
        schedule.tea_break_end = tea_end
        schedule._skip_dynamic_reschedule = True
        schedule.save()
        return schedule

    def create_task(self, title, minutes):
        return Task.objects.create(
            organization=self.org,
            title=title,
            assignee=self.user,
            created_by=self.user,
            estimated_hours=minutes / 60.0,
            estimated_minutes=minutes,
        )

    def local_hm(self, dt):
        local = to_org_tz(dt, self.org)
        return local.strftime("%H:%M")

    def local_date(self, dt):
        return to_org_tz(dt, self.org).date()

    def local_dt(self, date_text, hour, minute=0):
        return datetime.fromisoformat(f"{date_text}T{hour:02d}:{minute:02d}:00+05:30")

    def schedule_task(self, title, minutes, start_search_from=None, user=None):
        task = self.create_task(title, minutes)
        return SchedulerService.schedule_single_task_in_earliest_gap(
            task,
            start_search_from=start_search_from,
        )

    def assert_local_window(self, task_or_segment, start_hm, end_hm, start_date=None, end_date=None):
        start = task_or_segment["start"] if isinstance(task_or_segment, dict) else task_or_segment.planned_start
        end = task_or_segment["end"] if isinstance(task_or_segment, dict) else task_or_segment.planned_end
        self.assertEqual(self.local_hm(start), start_hm)
        self.assertEqual(self.local_hm(end), end_hm)
        if start_date:
            self.assertEqual(str(self.local_date(start)), start_date)
        if end_date:
            self.assertEqual(str(self.local_date(end)), end_date)

    def apply_recalculated_window(self, task, start_time=None, duration_minutes=None):
        recalculated = SchedulerService.recalculate_task_window(
            task,
            start_time=start_time or task.planned_start,
            duration_minutes=duration_minutes or task.total_estimated_minutes,
        )
        self.assertIsNotNone(recalculated)
        task.planned_start = recalculated["planned_start"]
        task.planned_end = recalculated["planned_end"]
        task.schedule_status = "SCHEDULED"
        task.schedule_reason = recalculated["schedule_reason"]
        task._skip_dynamic_reschedule = True
        task.save(update_fields=["planned_start", "planned_end", "schedule_status", "schedule_reason"])
        return recalculated

    def create_manual_scheduled_task(self, title, minutes, start_time, user=None):
        user = user or self.user
        task = Task.objects.create(
            organization=self.org,
            title=title,
            assignee=user,
            created_by=user,
            estimated_hours=minutes / 60.0,
            estimated_minutes=minutes,
            planned_start=start_time,
            schedule_status="SCHEDULED",
            is_auto_scheduled=True,
        )
        self.apply_recalculated_window(task, start_time=start_time, duration_minutes=minutes)
        return task

    def create_second_user(self):
        other = get_user_model().objects.create_user(
            email="second-assignee@example.com",
            password="password",
        )
        OrganizationMembership.objects.create(
            organization=self.org,
            user=other,
            role="member",
            is_active=True,
        )
        return other

    @patch("tasks.services.scheduler.timezone.now")
    def test_basic_task_creation_with_default_schedule_has_correct_duration(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T04:00:00+00:00")

        task = self.schedule_task("Basic 1h", 60)

        self.assertEqual(task.schedule_status, "SCHEDULED")
        self.assert_local_window(task, "10:00", "11:00", "2026-06-29", "2026-06-29")

    @patch("tasks.services.scheduler.timezone.now")
    def test_duration_calculation_for_common_task_lengths(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T04:00:00+00:00")
        self.set_user_schedule(
            work_start=time(10, 0),
            work_end=time(22, 0),
            lunch_start=time(22, 0),
            lunch_end=time(22, 0),
            tea_start=time(22, 0),
            tea_end=time(22, 0),
        )

        cases = [
            ("30 minutes", 30, "10:00", "10:30"),
            ("1 hour", 60, "10:30", "11:30"),
            ("2 hours", 120, "11:30", "13:30"),
            ("3.5 hours", 210, "13:30", "17:00"),
        ]

        for title, minutes, expected_start, expected_end in cases:
            with self.subTest(title=title):
                task = self.schedule_task(title, minutes)
                self.assert_local_window(task, expected_start, expected_end)
                self.assertEqual(task.planned_end - task.planned_start, timedelta(minutes=minutes))

    @patch("tasks.services.scheduler.timezone.now")
    def test_change_estimated_hours_recalculates_end_time(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T04:00:00+00:00")
        self.set_user_schedule(time(10, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0))
        task = self.schedule_task("Editable duration", 60)
        old_start = task.planned_start

        task.estimated_hours = 2
        task.estimated_minutes = 120
        task.save(update_fields=["estimated_hours", "estimated_minutes"])
        recalculated = self.apply_recalculated_window(task, start_time=old_start, duration_minutes=120)

        self.assertEqual(recalculated["planned_start"], old_start)
        self.assert_local_window(task, "10:00", "12:00")

    @patch("tasks.services.scheduler.timezone.now")
    def test_change_scheduled_start_recalculates_end_time(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T04:00:00+00:00")
        self.set_user_schedule(time(10, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0))
        task = self.schedule_task("Editable start", 90)

        new_start = self.local_dt("2026-06-29", 12, 30)
        self.apply_recalculated_window(task, start_time=new_start, duration_minutes=90)

        self.assert_local_window(task, "12:30", "14:00")

    @patch("tasks.services.scheduler.timezone.now")
    def test_custom_work_end_time_pushes_tasks_after_end_to_next_day(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T04:00:00+00:00")
        self.set_user_schedule(time(10, 0), time(15, 0), time(15, 0), time(15, 0), time(15, 0), time(15, 0))

        first = self.schedule_task("Morning block", 300)
        second = self.schedule_task("Next day block", 60)

        self.assert_local_window(first, "10:00", "15:00", "2026-06-29", "2026-06-29")
        self.assert_local_window(second, "10:00", "11:00", "2026-06-30", "2026-06-30")

    def test_lunch_break_interruption_splits_anchored_task_around_lunch(self):
        self.set_user_schedule(time(10, 0), time(18, 0), time(13, 0), time(14, 0), time(18, 0), time(18, 0))
        task = self.create_task("Lunch split", 120)

        recalculated = self.apply_recalculated_window(
            task,
            start_time=self.local_dt("2026-06-29", 12, 0),
            duration_minutes=120,
        )

        self.assert_local_window(task, "12:00", "15:00")
        self.assertEqual(len(recalculated["segments"]), 2)
        self.assert_local_window(recalculated["segments"][0], "12:00", "13:00")
        self.assert_local_window(recalculated["segments"][1], "14:00", "15:00")

    @patch("tasks.services.scheduler.timezone.now")
    def test_new_task_pauses_over_lunch_instead_of_queueing(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T06:30:00+00:00")
        self.set_user_schedule(time(10, 0), time(18, 0), time(13, 0), time(14, 0), time(18, 0), time(18, 0))

        task = self.schedule_task("Lunch spanning new task", 120)

        self.assertEqual(task.schedule_status, "SCHEDULED")
        self.assert_local_window(task, "12:00", "15:00", "2026-06-29", "2026-06-29")

    def test_tea_break_interruption_splits_anchored_task_around_tea(self):
        self.set_user_schedule(time(10, 0), time(19, 0), time(13, 0), time(13, 0), time(17, 0), time(17, 30))
        task = self.create_task("Tea split", 90)

        recalculated = self.apply_recalculated_window(
            task,
            start_time=self.local_dt("2026-06-29", 16, 30),
            duration_minutes=90,
        )

        self.assert_local_window(task, "16:30", "18:30")
        self.assertEqual(len(recalculated["segments"]), 2)
        self.assert_local_window(recalculated["segments"][0], "16:30", "17:00")
        self.assert_local_window(recalculated["segments"][1], "17:30", "18:30")

    @patch("tasks.services.scheduler.timezone.now")
    def test_new_tasks_chain_from_custom_user_start_time(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T08:00:00+00:00")
        self.set_user_schedule(
            work_start=time(14, 0),
            work_end=time(22, 0),
            lunch_start=time(18, 0),
            lunch_end=time(19, 0),
            tea_start=time(20, 0),
            tea_end=time(20, 30),
        )

        first = SchedulerService.schedule_single_task_in_earliest_gap(self.create_task("Task 1", 120))
        second = SchedulerService.schedule_single_task_in_earliest_gap(self.create_task("Task 2", 60))

        self.assertEqual(first.schedule_status, "SCHEDULED")
        self.assertEqual(self.local_hm(first.planned_start), "14:00")
        self.assertEqual(self.local_hm(first.planned_end), "16:00")
        self.assertEqual(second.schedule_status, "SCHEDULED")
        self.assertEqual(self.local_hm(second.planned_start), "16:00")
        self.assertEqual(self.local_hm(second.planned_end), "17:00")

    @patch("tasks.services.scheduler.timezone.now")
    def test_single_task_scheduler_fills_existing_gap_without_repacking(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T04:00:00+00:00")
        self.set_user_schedule(
            work_start=time(10, 0),
            work_end=time(19, 0),
            lunch_start=time(13, 0),
            lunch_end=time(14, 0),
            tea_start=time(17, 0),
            tea_end=time(17, 30),
        )

        early = SchedulerService.schedule_single_task_in_earliest_gap(self.create_task("Early", 60))
        late = self.create_task("Pinned Late", 60)
        late.planned_start = datetime.fromisoformat("2026-06-29T08:30:00+00:00")
        late.planned_end = datetime.fromisoformat("2026-06-29T09:30:00+00:00")
        late.schedule_status = "SCHEDULED"
        late.is_auto_scheduled = False
        late.save(update_fields=["planned_start", "planned_end", "schedule_status", "is_auto_scheduled"])

        filler = SchedulerService.schedule_single_task_in_earliest_gap(self.create_task("Filler", 120))
        late.refresh_from_db()

        self.assertEqual(self.local_hm(early.planned_start), "10:00")
        self.assertEqual(self.local_hm(early.planned_end), "11:00")
        self.assertEqual(self.local_hm(filler.planned_start), "11:00")
        self.assertEqual(self.local_hm(filler.planned_end), "13:00")
        self.assertEqual(self.local_hm(late.planned_start), "14:00")
        self.assertEqual(self.local_hm(late.planned_end), "15:00")

    @patch("tasks.services.scheduler.timezone.now")
    def test_scheduler_uses_one_continuous_gap_instead_of_splitting_task(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T04:00:00+00:00")
        self.set_user_schedule(
            work_start=time(10, 0),
            work_end=time(16, 0),
            lunch_start=time(16, 0),
            lunch_end=time(16, 0),
            tea_start=time(16, 0),
            tea_end=time(16, 0),
        )

        occupied_early = SchedulerService.schedule_single_task_in_earliest_gap(self.create_task("10-11", 60))
        occupied_late = self.create_task("12-13", 60)
        occupied_late.planned_start = datetime.fromisoformat("2026-06-29T06:30:00+00:00")
        occupied_late.planned_end = datetime.fromisoformat("2026-06-29T07:30:00+00:00")
        occupied_late.schedule_status = "SCHEDULED"
        occupied_late.is_auto_scheduled = False
        occupied_late.save(update_fields=["planned_start", "planned_end", "schedule_status", "is_auto_scheduled"])

        task = SchedulerService.schedule_single_task_in_earliest_gap(self.create_task("Two hours", 120))

        self.assertEqual(self.local_hm(occupied_early.planned_start), "10:00")
        self.assertEqual(self.local_hm(occupied_early.planned_end), "11:00")
        self.assertEqual(task.schedule_status, "SCHEDULED")
        self.assertEqual(self.local_hm(task.planned_start), "13:00")
        self.assertEqual(self.local_hm(task.planned_end), "15:00")

        # The 11:00-12:00 gap is intentionally left unused because the full
        # 2-hour task cannot fit there as one continuous block.
        self.assertEqual(task.planned_end - task.planned_start, timedelta(minutes=120))

    @patch("tasks.services.scheduler.timezone.now")
    def test_scheduler_uses_remaining_current_day_capacity_before_next_day(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T04:00:00+00:00")
        self.set_user_schedule(
            work_start=time(10, 0),
            work_end=time(18, 0),
            lunch_start=time(18, 0),
            lunch_end=time(18, 0),
            tea_start=time(18, 0),
            tea_end=time(18, 0),
        )

        first = SchedulerService.schedule_single_task_in_earliest_gap(self.create_task("10-12", 120))
        second = SchedulerService.schedule_single_task_in_earliest_gap(self.create_task("12-14", 120))
        third = SchedulerService.schedule_single_task_in_earliest_gap(self.create_task("14-16", 120))

        self.assertEqual(self.local_hm(first.planned_start), "10:00")
        self.assertEqual(self.local_hm(first.planned_end), "12:00")
        self.assertEqual(self.local_hm(second.planned_start), "12:00")
        self.assertEqual(self.local_hm(second.planned_end), "14:00")
        self.assertEqual(third.schedule_status, "SCHEDULED")
        self.assertEqual(self.local_hm(third.planned_start), "14:00")
        self.assertEqual(self.local_hm(third.planned_end), "16:00")

    @patch("tasks.services.scheduler.timezone.now")
    def test_explicit_same_day_anchor_is_not_advanced_by_late_wall_clock(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T13:00:00+00:00")
        self.set_user_schedule(
            work_start=time(10, 0),
            work_end=time(18, 0),
            lunch_start=time(18, 0),
            lunch_end=time(18, 0),
            tea_start=time(18, 0),
            tea_end=time(18, 0),
        )

        existing = self.create_task("10-14", 240)
        existing.planned_start = datetime.fromisoformat("2026-06-29T04:30:00+00:00")
        existing.planned_end = datetime.fromisoformat("2026-06-29T08:30:00+00:00")
        existing.schedule_status = "SCHEDULED"
        existing.is_auto_scheduled = True
        existing.save(update_fields=["planned_start", "planned_end", "schedule_status", "is_auto_scheduled"])

        segments = SchedulerService.get_next_available_slot(
            self.user.id,
            120,
            self.org.id,
            start_search_from=existing.planned_end,
            user=self.user,
        )

        self.assertIsNotNone(segments)
        self.assertEqual(self.local_hm(segments[0]["start"]), "14:00")
        self.assertEqual(self.local_hm(segments[0]["end"]), "16:00")

    @patch("tasks.services.scheduler.timezone.now")
    def test_new_task_uses_remaining_current_day_after_last_task_before_next_day(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T13:00:00+00:00")
        self.set_user_schedule(
            work_start=time(10, 0),
            work_end=time(18, 0),
            lunch_start=time(18, 0),
            lunch_end=time(18, 0),
            tea_start=time(18, 0),
            tea_end=time(18, 0),
        )
        existing = self.create_task("Existing 10-14", 240)
        existing.planned_start = datetime.fromisoformat("2026-06-29T04:30:00+00:00")
        existing.planned_end = datetime.fromisoformat("2026-06-29T08:30:00+00:00")
        existing.schedule_status = "SCHEDULED"
        existing.is_auto_scheduled = True
        existing.save(update_fields=["planned_start", "planned_end", "schedule_status", "is_auto_scheduled"])

        task = SchedulerService.schedule_single_task_in_earliest_gap(self.create_task("Uses 14-16", 120))

        self.assertEqual(task.schedule_status, "SCHEDULED")
        self.assertEqual(self.local_hm(task.planned_start), "14:00")
        self.assertEqual(self.local_hm(task.planned_end), "16:00")
        self.assertEqual(str(self.local_date(task.planned_start)), "2026-06-29")

    @patch("tasks.services.scheduler.timezone.now")
    def test_cascade_recalculates_changed_task_and_shifts_later_tasks_without_overlap(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T04:00:00+00:00")
        self.set_user_schedule(
            work_start=time(10, 0),
            work_end=time(19, 0),
            lunch_start=time(13, 0),
            lunch_end=time(14, 0),
            tea_start=time(17, 0),
            tea_end=time(17, 30),
        )

        first = SchedulerService.schedule_single_task_in_earliest_gap(self.create_task("Task 1", 120))
        second = SchedulerService.schedule_single_task_in_earliest_gap(self.create_task("Task 2", 60))
        third = SchedulerService.schedule_single_task_in_earliest_gap(self.create_task("Task 3", 60))

        old_start = first.planned_start
        old_end = first.planned_end
        first.estimated_hours = 4
        first.estimated_minutes = 240
        first.save(update_fields=["estimated_hours", "estimated_minutes"])

        SchedulerService.cascade_reschedule_tasks(self.user, first.id, old_start, old_end)

        first.refresh_from_db()
        second.refresh_from_db()
        third.refresh_from_db()

        self.assertEqual(self.local_hm(first.planned_start), "10:00")
        self.assertEqual(self.local_hm(first.planned_end), "15:00")
        self.assertEqual(self.local_hm(second.planned_start), "15:00")
        self.assertEqual(self.local_hm(second.planned_end), "16:00")
        self.assertEqual(self.local_hm(third.planned_start), "16:00")
        self.assertEqual(self.local_hm(third.planned_end), "17:00")
        self.assertLessEqual(first.planned_end, second.planned_start)
        self.assertLessEqual(second.planned_end, third.planned_start)

    @patch("tasks.services.scheduler.timezone.now")
    def test_cascade_shifts_later_tasks_when_middle_task_start_changes(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T04:00:00+00:00")
        self.set_user_schedule(time(10, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0))
        first = self.schedule_task("Task 1", 60)
        second = self.schedule_task("Task 2", 60)
        third = self.schedule_task("Task 3", 60)
        fourth = self.schedule_task("Task 4", 60)

        old_start = second.planned_start
        old_end = second.planned_end
        second.planned_start = self.local_dt("2026-06-29", 13, 0)
        second._skip_dynamic_reschedule = True
        second.save(update_fields=["planned_start"])
        SchedulerService.cascade_reschedule_tasks(self.user, second.id, old_start, old_end)

        first.refresh_from_db()
        second.refresh_from_db()
        third.refresh_from_db()
        fourth.refresh_from_db()

        self.assert_local_window(first, "10:00", "11:00")
        self.assert_local_window(second, "13:00", "14:00")
        self.assert_local_window(third, "14:00", "15:00")
        self.assert_local_window(fourth, "15:00", "16:00")

    @patch("tasks.services.scheduler.timezone.now")
    def test_shorten_middle_task_moves_later_tasks_forward(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T04:00:00+00:00")
        self.set_user_schedule(time(10, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0))
        first = self.schedule_task("Task 1", 120)
        second = self.schedule_task("Task 2", 120)
        third = self.schedule_task("Task 3", 60)

        old_start = second.planned_start
        old_end = second.planned_end
        second.estimated_hours = 1
        second.estimated_minutes = 60
        second._skip_dynamic_reschedule = True
        second.save(update_fields=["estimated_hours", "estimated_minutes"])
        SchedulerService.cascade_reschedule_tasks(self.user, second.id, old_start, old_end)

        first.refresh_from_db()
        second.refresh_from_db()
        third.refresh_from_db()
        self.assert_local_window(first, "10:00", "12:00")
        self.assert_local_window(second, "12:00", "13:00")
        self.assert_local_window(third, "13:00", "14:00")

    @patch("tasks.services.scheduler.timezone.now")
    def test_lengthen_middle_task_moves_later_tasks_backward(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T04:00:00+00:00")
        self.set_user_schedule(time(10, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0))
        first = self.schedule_task("Task 1", 60)
        second = self.schedule_task("Task 2", 60)
        third = self.schedule_task("Task 3", 60)

        old_start = second.planned_start
        old_end = second.planned_end
        second.estimated_hours = 2
        second.estimated_minutes = 120
        second._skip_dynamic_reschedule = True
        second.save(update_fields=["estimated_hours", "estimated_minutes"])
        SchedulerService.cascade_reschedule_tasks(self.user, second.id, old_start, old_end)

        first.refresh_from_db()
        second.refresh_from_db()
        third.refresh_from_db()
        self.assert_local_window(first, "10:00", "11:00")
        self.assert_local_window(second, "11:00", "13:00")
        self.assert_local_window(third, "13:00", "14:00")

    def test_multi_day_anchored_task_spans_working_days_correctly(self):
        self.set_user_schedule(time(10, 0), time(15, 0), time(15, 0), time(15, 0), time(15, 0), time(15, 0))
        task = self.create_task("Multi-day", 480)

        recalculated = self.apply_recalculated_window(
            task,
            start_time=self.local_dt("2026-06-29", 10, 0),
            duration_minutes=480,
        )

        self.assert_local_window(task, "10:00", "13:00", "2026-06-29", "2026-06-30")
        self.assertEqual(len(recalculated["segments"]), 2)
        self.assert_local_window(recalculated["segments"][0], "10:00", "15:00", "2026-06-29", "2026-06-29")
        self.assert_local_window(recalculated["segments"][1], "10:00", "13:00", "2026-06-30", "2026-06-30")

    @patch("tasks.services.scheduler.timezone.now")
    def test_profile_break_change_reschedules_existing_tasks(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T04:00:00+00:00")
        self.set_user_schedule(time(10, 0), time(18, 0), time(13, 0), time(14, 0), time(18, 0), time(18, 0))
        first = self.schedule_task("Before break change", 180)
        second = self.schedule_task("After break change", 60)

        self.set_user_schedule(time(10, 0), time(18, 0), time(12, 0), time(13, 0), time(18, 0), time(18, 0))
        SchedulerService.reschedule_user_future_tasks(self.user.id)

        first.refresh_from_db()
        second.refresh_from_db()
        # Break changes keep the original chain order and pause affected
        # tasks across the new break instead of overlapping it.
        self.assert_local_window(first, "10:00", "14:00", "2026-06-29", "2026-06-29")
        self.assertEqual(first.schedule_status, "SCHEDULED")
        self.assert_local_window(second, "14:00", "15:00", "2026-06-29", "2026-06-29")
        self.assertLessEqual(first.planned_end, second.planned_start)

    @patch("tasks.services.scheduler.timezone.now")
    def test_work_start_change_shifts_existing_tasks(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T04:00:00+00:00")
        self.set_user_schedule(time(10, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0))
        first = self.schedule_task("First", 60)
        second = self.schedule_task("Second", 60)

        self.set_user_schedule(time(14, 0), time(22, 0), time(22, 0), time(22, 0), time(22, 0), time(22, 0))
        SchedulerService.reschedule_user_future_tasks(self.user.id)

        first.refresh_from_db()
        second.refresh_from_db()
        self.assert_local_window(first, "14:00", "15:00")
        self.assert_local_window(second, "15:00", "16:00")

    @patch("tasks.services.scheduler.timezone.now")
    def test_half_day_change_pushes_overflow_to_next_days(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T04:00:00+00:00")
        self.set_user_schedule(time(10, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0))
        first = self.schedule_task("First", 180)
        second = self.schedule_task("Second", 180)

        self.set_user_schedule(time(10, 0), time(15, 0), time(15, 0), time(15, 0), time(15, 0), time(15, 0))
        SchedulerService.reschedule_user_future_tasks(self.user.id)

        first.refresh_from_db()
        second.refresh_from_db()
        self.assert_local_window(first, "10:00", "13:00", "2026-06-29", "2026-06-29")
        self.assert_local_window(second, "10:00", "13:00", "2026-06-30", "2026-06-30")

    @patch("tasks.services.scheduler.timezone.now")
    def test_overnight_shift_schedules_across_midnight(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T12:00:00+00:00")
        self.set_user_schedule(time(18, 0), time(4, 0), time(4, 0), time(4, 0), time(4, 0), time(4, 0))

        first = self.schedule_task("Night first", 240)
        second = self.schedule_task("Night second", 180)

        self.assert_local_window(first, "18:00", "22:00", "2026-06-29", "2026-06-29")
        self.assert_local_window(second, "22:00", "01:00", "2026-06-29", "2026-06-30")

    @patch("tasks.services.scheduler.timezone.now")
    def test_queue_after_seven_full_working_days(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T04:00:00+00:00")
        self.set_user_schedule(time(10, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0))

        for offset in range(7):
            day = self.local_dt("2026-06-29", 10, 0) + timedelta(days=offset)
            self.create_manual_scheduled_task(f"Full day {offset}", 480, day)

        queued = self.schedule_task("No capacity", 60)

        self.assertEqual(queued.schedule_status, "QUEUED")
        self.assertIsNone(queued.planned_start)
        self.assertIsNone(queued.planned_end)

    @patch("tasks.services.scheduler.timezone.now")
    def test_short_task_does_not_use_tiny_end_of_day_remainder(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T04:00:00+00:00")
        self.set_user_schedule(time(10, 0), time(18, 0), time(13, 0), time(14, 0), time(18, 0), time(18, 0))
        self.create_manual_scheduled_task("Almost full", 405, self.local_dt("2026-06-29", 10, 0))

        task = self.schedule_task("Needs 30 minutes", 30)

        self.assert_local_window(task, "10:00", "10:30", "2026-06-30", "2026-06-30")

    @patch("tasks.services.scheduler.timezone.now")
    def test_partial_current_day_does_not_reduce_seven_full_day_scan_window(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T13:00:00+00:00")
        self.set_user_schedule(time(10, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0))
        self.create_manual_scheduled_task("Current day partial", 300, self.local_dt("2026-06-29", 10, 0))

        for offset in range(1, 7):
            day = self.local_dt("2026-06-29", 10, 0) + timedelta(days=offset)
            self.create_manual_scheduled_task(f"Full future day {offset}", 480, day)

        task = self.schedule_task("Six hour task", 360)

        self.assertEqual(task.schedule_status, "SCHEDULED")
        self.assert_local_window(task, "10:00", "16:00", "2026-07-06", "2026-07-06")

    @patch("tasks.services.scheduler.timezone.now")
    def test_small_remaining_time_moves_one_hour_task_to_next_day(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T04:00:00+00:00")
        self.set_user_schedule(time(10, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0))
        self.create_manual_scheduled_task("Almost full day", 465, self.local_dt("2026-06-29", 10, 0))

        task = self.schedule_task("Needs one hour", 60)

        self.assert_local_window(task, "10:00", "11:00", "2026-06-30", "2026-06-30")

    @patch("tasks.services.scheduler.timezone.now")
    def test_gap_filling_uses_earliest_gap_for_small_task(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T04:00:00+00:00")
        self.set_user_schedule(time(10, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0))
        self.create_manual_scheduled_task("10-11", 60, self.local_dt("2026-06-29", 10, 0))
        self.create_manual_scheduled_task("11:30-12:30", 60, self.local_dt("2026-06-29", 11, 30))

        task = self.schedule_task("Gap filler", 30)

        self.assert_local_window(task, "11:00", "11:30", "2026-06-29", "2026-06-29")

    @patch("tasks.services.scheduler.timezone.now")
    def test_schedule_persists_after_save_and_refresh(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T04:00:00+00:00")
        self.set_user_schedule(time(10, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0))
        task = self.schedule_task("Persistent schedule", 90)
        original_start = task.planned_start
        original_end = task.planned_end

        task.title = "Persistent schedule renamed"
        task.save(update_fields=["title"])
        refreshed = Task.objects.get(id=task.id)

        self.assertEqual(refreshed.planned_start, original_start)
        self.assertEqual(refreshed.planned_end, original_end)
        self.assertEqual(refreshed.schedule_status, "SCHEDULED")

    @patch("tasks.services.scheduler.timezone.now")
    def test_multiple_users_respect_their_own_schedules(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T04:00:00+00:00")
        other = self.create_second_user()
        self.set_user_schedule(time(10, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0))
        other_schedule, _ = UserWorkingSchedule.objects.get_or_create(user=other)
        other_schedule.work_start_time = time(14, 0)
        other_schedule.work_end_time = time(22, 0)
        other_schedule.lunch_break_start = time(22, 0)
        other_schedule.lunch_break_end = time(22, 0)
        other_schedule.tea_break_start = time(22, 0)
        other_schedule.tea_break_end = time(22, 0)
        other_schedule._skip_dynamic_reschedule = True
        other_schedule.save()

        own_task = self.schedule_task("Primary user", 60)
        other_task = Task.objects.create(
            organization=self.org,
            title="Second user",
            assignee=other,
            created_by=other,
            estimated_hours=1,
            estimated_minutes=60,
        )
        other_task = SchedulerService.schedule_single_task_in_earliest_gap(other_task)

        self.assert_local_window(own_task, "10:00", "11:00")
        self.assertEqual(to_org_tz(other_task.planned_start, self.org).strftime("%H:%M"), "14:00")
        self.assertEqual(to_org_tz(other_task.planned_end, self.org).strftime("%H:%M"), "15:00")

    def test_profile_schedule_validation_uses_custom_work_end_time(self):
        serializer = UserSerializer(
            instance=self.user,
            data={
                "working_schedule": {
                    "work_start_time": "14:00:00",
                    "work_end_time": "18:00:00",
                    "lunch_break_start": "15:00:00",
                    "lunch_break_end": "15:30:00",
                    "tea_break_start": "17:00:00",
                    "tea_break_end": "17:15:00",
                }
            },
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    @patch("tasks.services.scheduler.timezone.now")
    def test_profile_schedule_change_notifies_owner_and_task_creator(self, mock_now):
        mock_now.return_value = datetime.fromisoformat("2026-06-29T04:00:00+00:00")
        creator = self.create_second_user()
        self.org.owner = creator
        self.org.save(update_fields=["owner"])
        OrganizationMembership.objects.filter(organization=self.org, user=creator).update(role="owner")
        owner_membership = OrganizationMembership.objects.get(organization=self.org, user=self.user)
        owner_membership.role = "member"
        owner_membership.save()

        self.set_user_schedule(time(10, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0), time(18, 0))
        task = self.create_task("Creator-owned task", 60)
        task.created_by = creator
        task.save(update_fields=["created_by"])

        from users.views import _notify_schedule_change_watchers
        old_schedule = {
            'work_start_time': time(10, 0),
            'work_end_time': time(18, 0),
            'lunch_break_start': time(18, 0),
            'lunch_break_end': time(18, 0),
            'tea_break_start': time(18, 0),
            'tea_break_end': time(18, 0),
        }
        new_schedule = {
            **old_schedule,
            'work_start_time': time(14, 0),
            'work_end_time': time(22, 0),
        }

        _notify_schedule_change_watchers(self.user, self.org, old_schedule, new_schedule)

        notification = Notification.objects.get(user=creator, title="Member Schedule Changed")
        self.assertEqual(notification.notification_type, "task_rescheduled")
        self.assertIn("Work start: 10:00 -> 14:00", notification.message)
