# 6 Scheduler Documentation

## Scheduler Overview

The scheduler is the most important business subsystem. Its current implementation lives primarily in:

- `backend/tasks/services/calendar.py`
- `backend/tasks/services/scheduler.py`
- `backend/tasks/services/preview.py`
- legacy utility file `backend/tasks/schedule_utils.py`

The active service-based scheduler scans available intervals for an assignee and stores planned task windows on the `Task` model. It can return segmented schedules when a task spans multiple free intervals.

## Scheduling Data Model

Task scheduling fields:

| Field | Meaning |
|---|---|
| `planned_start` | Calculated or manually pinned start datetime |
| `planned_end` | Calculated or manually pinned end datetime |
| `schedule_status` | `SCHEDULED`, `QUEUED`, or `COMPLETED` |
| `queue_position` | Position for queued tasks |
| `is_auto_scheduled` | Whether scheduler may manage the task |
| `schedule_reason` | Human reason or JSON segment list |
| `last_scheduler_run` | Last time scheduler processed task |

Duration fields:

- `estimated_minutes` is preferred when set.
- `estimated_hours` is converted to minutes otherwise.
- Default duration is 60 minutes when no estimate exists.

## Task Creation Flow

1. Frontend posts task data to `/tasks/create/`.
2. Backend validates organization and related users.
3. Serializer maps `assignees[0]` to single `assignee`.
4. Members cannot assign tasks to admins/owners.
5. Watchers and visibility users are set.
6. For specific visibility, creator and all owner/admin users are added to visible users.
7. If planned start/end is present, code sets `is_auto_scheduled=False`.
8. `apply_automatic_task_schedule()` is still called.
9. Scheduler attempts to place assigned task.
10. Response returns task plus schedule details.

Current concern: the create flow marks manual tasks as not auto-scheduled but still invokes automatic scheduling, so manual pinning behavior is ambiguous.

## Schedule Preview

Endpoint: `POST /organizations/{org_id}/tasks/schedule-preview/`

Request:

```json
{
  "assignee": "user-uuid",
  "estimated_hours": 2.5,
  "task_id": "optional-task-uuid",
  "start_search_from": "optional ISO datetime"
}
```

Behavior:

- Converts `estimated_hours` to minutes.
- If editing and no start anchor is supplied, uses existing task `planned_start`.
- Calls `get_schedule_preview()`.
- Returns local organization-time ISO strings for `planned_start`, `planned_end`, and `segments`.
- Returns queue message when no capacity exists within the scan window.

Current concern: this view writes debug logs to an absolute path inside the repository.

## Working Hours

Organization settings:

- `working_start_time`, default 10:00
- `working_end_time`, default 19:00
- `working_days`, default Mon-Fri `[0,1,2,3,4]`
- lunch break, default 13:00-14:00
- tea break, default 17:00-17:30
- `additional_breaks`
- `maximum_scan_days`, default 7
- `timezone`, default `Asia/Kolkata`

User schedule can override:

- work start
- work end
- lunch break
- tea break

The `UserWorkingSchedule.save()` method currently forces `work_end_time = work_start_time + 10 hours`, clamps lunch/tea inside that 10-hour window, caps lunch at 60 minutes, and caps tea at 30 minutes.

## Break Handling

`get_working_intervals()` converts a workday into available intervals by subtracting lunch, tea, and additional organization breaks. Breaks are normalized for overnight shifts by adding one day when break times are before the work start time.

Example:

| Work | Lunch | Tea | Resulting Intervals |
|---|---|---|---|
| 10:00-19:00 | 13:00-14:00 | 17:00-17:30 | 10:00-13:00, 14:00-17:00, 17:30-19:00 |

## Gap Filling

The scheduler uses `_get_busy_slots()` to find existing planned tasks for the assignee and `_subtract_intervals()` to subtract those occupied windows from working intervals. It scans free intervals from the anchor time and accumulates segments until the required minutes are allocated.

This means the current scheduler can fill gaps before later scheduled tasks, not only append after the last task.

## Queue Behavior

A task becomes queued when no sufficient capacity is found within `maximum_scan_days` working days. The scheduler clears planned start/end, sets:

- `schedule_status='QUEUED'`
- `queue_position` incrementally
- `schedule_reason='Waiting For Capacity'`

Queued tasks are reconsidered by:

- manual schedule endpoint
- run scheduler endpoint
- Celery scheduled job
- dynamic reschedule triggers

## Rescheduling

Rescheduling is triggered when:

- task scheduling fields, duration, due date, priority, assignee, or status changes
- task is deleted
- user working schedule changes
- approved/cancelled leave changes
- Celery beat runs every 30 minutes

Important methods:

- `schedule_tasks_for_assignee()`: schedules queued and future scheduled tasks for one assignee.
- `cascade_reschedule_tasks()`: reflows tasks after a changed task.
- `reschedule_user_future_tasks()`: schedules future tasks for all orgs where a user has tasks.
- `reschedule_from_datetime()`: currently delegates to full assignee scheduling.

## Task Editing

When updating task details:

- If start changes but end does not, backend recalculates end using scheduler.
- If estimate changes but end does not, backend recalculates end.
- If end changes, backend recalculates estimated duration using working-hour calculation.
- If start/end changes, task is pinned with `is_auto_scheduled=False`.
- A post-commit reflow may cascade subsequent tasks.

Current concern: update code passes an organization membership object to `calculate_working_hours()` where the calendar service expects a user object. This may prevent user-specific schedule overrides from applying correctly.

## Task Duration and Minute Calculation

Rules:

- `estimated_hours -> estimated_minutes = hours * 60`
- `estimated_minutes -> estimated_hours = minutes / 60`
- Scheduler uses `Task.total_estimated_minutes`.
- Task tickets track actual `time_spent_minutes`.
- Task status timing adds elapsed minutes when a ticket leaves `in_progress`.

## Overnight Shifts

The service scheduler supports overnight shifts by:

- Extending work end into next day when `work_end < work_start`.
- Normalizing breaks that occur after midnight.
- Determining the logical working day if current time is in the early morning portion of an overnight shift.

Limitations:

- Some legacy/frontend utility functions handle overnight differently or not at all.
- User schedule save forces a 10-hour shift and may produce next-day work end, but serializer duration calculations are separate.

## Current Limitations and Possible Bugs

| Area | Observation |
|---|---|
| Duplicate scheduler logic | New `tasks/services/*` coexists with older `tasks/schedule_utils.py` and frontend schedule utilities. |
| Missing method | Wrapper `reschedule_subsequent_tasks()` calls `SchedulerService.reschedule_subsequent_tasks`, but that class method is absent. |
| Manual pin ambiguity | Create flow sets `is_auto_scheduled=False` then still auto-schedules. |
| Debug file writes | Schedule preview writes to hard-coded absolute path. |
| Frontend/backend drift | Frontend exposes scheduling APIs that are commented out or not implemented. |
| User schedule parameter bug | Some calendar calls pass membership instead of user. |
| Queue position in cascade | Cascade queued branch does not set a new queue position. |
| Status mismatch | Scheduler excludes statuses like `cancelled`/`archived`, but these are not defined task status choices. |
| Segment storage | `schedule_reason` stores JSON segments or plain text, mixing data and reason. |
| Race conditions | Concurrent scheduling runs for the same assignee can compete despite transaction use, especially across Celery/manual/API triggers. |
| Timezones | Backend returns localized ISO strings; frontend also converts dates locally. QA is needed for DST and non-India timezones. |
