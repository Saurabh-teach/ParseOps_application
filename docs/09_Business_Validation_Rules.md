# 9 Business Rules and Validation Rules

## Existing Business Rules

| Domain | Rule |
|---|---|
| Authentication | Email is the unique login identifier. |
| Registration/login | OTP verification is required in current custom flow. |
| Organization | Organization slugs are generated from names. |
| Organization | Default working days are Monday-Friday. |
| Membership | A user can have one membership per organization. |
| Membership | An organization must retain at least one active owner. |
| Invitation | Invitations have unique tokens and status. |
| Join request | A user cannot submit duplicate pending join requests for the same organization. |
| Goals | Goal titles are unique per organization among non-deleted goals. |
| Goals | KR progress is clamped to 0-100. |
| Goals | Goal progress is average KR progress, or task completion percentage when no KRs exist. |
| Tasks | Task titles are unique within a goal among non-deleted tasks. |
| Tasks | Canonical task assignment is single-assignee, with `assignees` retained for compatibility. |
| Tasks | Regular members cannot assign tasks to admins/owners. |
| Tasks | Owner/admin users can view all org tasks. |
| Tasks | Members can view organization tasks, created tasks, assigned tasks, watched tasks, visible tasks, and shared tasks. |
| Scheduling | Assigned tasks enter scheduling; unassigned tasks remain queued with "No assignee". |
| Scheduling | Scheduler scans up to organization `maximum_scan_days`. |
| Scheduling | Scheduler skips non-working days and approved leave dates. |
| Scheduling | Scheduler subtracts planned non-done tasks from working intervals. |
| Scheduling | Tasks with insufficient capacity become queued. |
| Leaves | Leave start date must be before or equal to end date. |
| Leaves | Pending/approved leave overlap is blocked. |
| Leaves | Half-day leave counts as 0.5 day. |
| Leaves | Default leave balance is auto-created as 10 days for applicable leave types. |
| Working schedule | Lunch break maximum is 60 minutes. |
| Working schedule | Tea break maximum is 30 minutes. |
| Working schedule | Breaks must be inside a 10-hour shift and cannot overlap. |
| Tickets | Task ticket status changes recalculate master task status. |
| Feedback | One feedback per user per task. |

## Validation Rules

### Working Hours

- User work start can be supplied.
- Work end is read-only in profile serializer and computed by model save.
- Lunch and tea breaks are parsed from flat multipart fields or nested schedule data.
- Breaks before work start may be treated as next-day breaks for overnight shifts.
- Serializer prevents lunch/tea overlap and breaks outside the 10-hour shift.

### Task Duration

- Estimated hours and minutes are synchronized.
- Actual hours and minutes are synchronized.
- Custom reminders require `reminder_duration_minutes`.
- Task due-period validation rejects assigning a user who is on approved leave during task dates.

### Queue

- Queue is entered when no schedule slot is found.
- Queue position is assigned during `schedule_tasks_for_assignee()`.
- Queued tasks can be promoted when scheduler reruns and capacity exists.

### Rescheduling

- Task edits trigger post-commit cascading when key scheduling fields change.
- User working schedule changes trigger future rescheduling.
- Approved/cancelled leave changes trigger future rescheduling.

## Missing Rules

- Explicit holiday calendar beyond leave requests.
- Maximum task duration allowed.
- Whether a task may be segmented across multiple days or must be continuous.
- Clear policy for manual tasks during automatic scheduling.
- Queue priority override rules.
- Role-level rules for who can edit organization scheduling settings.
- SLA for overdue notification/reminder processing.
- Exact rule for group tasks since `required_assignees` exists but canonical assignment is single-user.

## Conflicting or Incomplete Rules

- Task model supports single assignee, but UI/API naming still uses `assignees`.
- Smart-assignment frontend APIs exist, but backend endpoints are commented out.
- Scheduler excludes statuses not present in model choices.
- `schedule_reason` is both a human status reason and a JSON segment carrier.
- Frontend assumes some scheduling calculations that differ from backend organization settings.

## Recommended Rule Clarifications

- Define "manual scheduled task" as pinned and excluded from auto-reflow unless explicitly unlocked.
- Store schedule segments in a dedicated structured field/model.
- Define whether queued task order is strict FIFO, score-based, priority-based, or manager-controlled.
- Define cross-midnight shift behavior in product terms.
- Define how leaves affect existing in-progress tasks.
- Define whether owners/admins are always visible on private goals/tasks.
