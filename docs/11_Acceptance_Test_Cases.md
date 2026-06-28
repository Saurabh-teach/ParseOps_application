# 13 Acceptance Criteria

## Authentication

- User can register with unique email and verify OTP.
- User can login, verify OTP, receive JWT tokens, and refresh tokens.
- Logout invalidates/blacklists refresh token.
- Password reset and email change require OTP verification.
- Profile updates persist user fields and working schedule.

## Organizations

- Authenticated user can create an organization and become owner.
- Slug is generated and unique.
- Users can request to join public organizations.
- Owners/admins can approve/reject join requests.
- Owners/admins can invite users, cancel invites, and manage members.
- Last active owner cannot be removed or demoted.

## Goals

- Users with permission can create/update/delete goals.
- Duplicate goal title in same organization is rejected.
- Key result create/update/delete recalculates goal progress.
- If no key results exist, linked task completion drives goal progress.
- Goal chat room is created for new goals.

## Tasks

- Users with permission can create tasks under an organization and optionally a goal.
- Related assignee/watcher/visible users must be active organization members.
- Regular members cannot assign work to admins/owners.
- Specific-visibility tasks include creator and management users.
- Task details respect visibility rules.
- Updating start/end/estimate keeps duration fields synchronized.
- Soft-deleted tasks leave active lists and appear in trash.
- Comments, replies, mentions, and attachments are visible on allowed tasks.
- Task tickets sync master task status.
- Submissions, feedback, and extension requests persist correctly.

## Scheduler

- New assigned task receives scheduled start/end if capacity exists.
- Task is queued when no capacity exists within scan window.
- Scheduler skips lunch, tea, additional breaks, weekends/non-working days, and approved leaves.
- Scheduler uses user working schedule when present.
- Overnight shifts schedule across midnight correctly.
- Editing a task reflows subsequent auto-scheduled tasks.
- Updating user working schedule reflows future tasks.
- Approved/cancelled leave reflows future tasks.
- Queue tasks become scheduled when capacity opens.

## Notifications

- Task, goal, extension, organization, and chat events create notifications.
- User can mark one or all notifications read.
- User can clear notifications.
- Websocket notification path connects with valid auth/session context.
- Web push subscription can be saved.

## Frontend

- Auth token is attached to API requests.
- Expired access token refreshes automatically when refresh token is valid.
- Workspace access loss triggers UI reset.
- Task create/edit forms show schedule preview and resulting planned times.
- Dashboard filters update analytics.
- Calendar displays relevant planned work/events.
- Queue UI allows scheduling/assigning flows that match backend support.

# Test Cases

| ID | Scenario | Expected Result |
|---|---|---|
| AUTH-001 | Register duplicate email | Validation error |
| AUTH-002 | Login with wrong password | Authentication error |
| AUTH-003 | Verify expired OTP | OTP rejected |
| ORG-001 | Remove last owner | Validation error |
| ORG-002 | Member requests same org twice | Duplicate pending request rejected |
| GOAL-001 | Create duplicate goal title in org | Validation error |
| KR-001 | Update KR current value | Goal progress recalculates |
| TASK-001 | Create task with non-member assignee | 400 error |
| TASK-002 | Member assigns task to owner | 403 error |
| TASK-003 | Private task viewed by unrelated member | 403 error |
| TASK-004 | End time changed | Estimated hours/minutes recalculate |
| TASK-005 | Ticket changed to done | Master status recalculates |
| LEAVE-001 | Overlapping leave request | Validation error |
| LEAVE-002 | Insufficient leave balance | Validation error |
| SCHED-001 | 2-hour task before lunch | Ends before lunch if capacity exists |
| SCHED-002 | 3-hour task starting 12:00 with lunch | Segment skips lunch |
| SCHED-003 | Task exceeds scan capacity | Task queued |
| SCHED-004 | Approved leave tomorrow | Scheduler skips leave date |
| SCHED-005 | Overnight 22:00 start | Work intervals cross midnight |
| SCHED-006 | Existing task leaves gap | New task fits earliest gap |
| API-001 | Missing `estimated_hours` on preview | 400 error |
| API-002 | Invalid CSV extension | 400 error |
| FE-001 | Expired access token with valid refresh | Request retries successfully |
| FE-002 | Removed workspace member receives 403 | `workspace_access_lost` event fires |
