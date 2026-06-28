# 5 API Documentation

All protected endpoints use JWT bearer authentication unless noted. Base URL in the frontend is `http://127.0.0.1:8000/api`.

## Authentication and Users

| Method | Endpoint | Purpose | Request | Response |
|---|---|---|---|---|
| POST | `/token/` | SimpleJWT token obtain | email/password depending serializer | access/refresh |
| POST | `/token/refresh/` | Refresh JWT | `refresh` | new access/refresh |
| POST | `/users/register/` | Start registration | `email`, `password` | OTP flow message |
| POST | `/users/verify-registration-otp/` | Complete registration | `email`, `otp` | tokens/user |
| POST | `/users/login/` | Start login | `email`, `password` | OTP flow message |
| POST | `/users/verify-login-otp/` | Complete login | `email`, `otp` | tokens/user |
| POST | `/users/logout/` | Blacklist refresh token | `refresh` | success |
| GET/PATCH | `/users/profile/` | Retrieve/update profile and working schedule | user fields, multipart supported | user profile |
| POST | `/users/request-email-change/` | Request email change | `new_email`, `password` | OTP message |
| POST | `/users/verify-email-change/` | Verify email change | `new_email`, `otp` | success |
| POST | `/users/change-password/` | Change password | `email`, `new_password` | success |
| POST | `/users/forgot-password/` | Start reset | `email` | OTP/token message |
| POST | `/users/reset-password-verify/` | Verify reset OTP | `email`, `otp`, `password` | success |
| GET | `/users/list/` | User list | query params | users |

## Leave Management

| Method | Endpoint | Purpose |
|---|---|---|
| GET/POST | `/users/leaves/` | List/create leaves |
| GET/PATCH/DELETE | `/users/leaves/{id}/` | Retrieve/update/delete leave |
| POST | `/users/leaves/{id}/approve/` | Approve leave |
| POST | `/users/leaves/{id}/reject/` | Reject with reason |
| POST | `/users/leaves/{id}/cancel/` | Cancel with reason |
| GET | `/users/leave-balances/` | List balances |

Validation includes date ordering, overlap prevention, balance checking, half-day calculation, and default balance creation for missing balances.

## Organizations

| Method | Endpoint | Purpose |
|---|---|---|
| GET/POST | `/organizations/` | List/create organizations |
| GET/PATCH/DELETE | `/organizations/{id}/` | Retrieve/update/delete/deactivate organization |
| POST | `/organizations/{id}/deactivate/` | Deactivate workspace |
| POST | `/organizations/{id}/reactivate/` | Reactivate workspace |
| GET | `/organizations/my-workspaces/` | Current user's workspaces |
| POST | `/organizations/{id}/join-request/` | Request membership |
| GET | `/organizations/{id}/join-requests/` | List pending join requests |
| POST | `/organizations/{id}/manage-request/` | Approve/reject request |
| POST | `/organizations/{id}/invite/` | Invite by email |
| GET | `/organizations/{id}/pending-invitations/` | Pending invites |
| POST | `/organizations/{id}/cancel-invitation/` | Cancel invite |
| POST | `/organizations/accept-invitation/` | Accept invitation |
| POST | `/organizations/decline-invitation/` | Decline invitation |
| GET | `/organizations/{id}/members/` | List members |
| GET | `/organizations/{id}/members/{member_id}/` | Member detail |
| POST | `/organizations/{id}/remove-member/` | Deactivate membership |
| POST | `/organizations/{id}/restore-member/` | Restore membership |
| POST | `/organizations/{id}/change-role/` | Change role |
| POST | `/organizations/{id}/change-permissions/` | Update custom permissions |
| GET | `/organizations/{id}/calendar-events/` | Organization calendar events |
| GET | `/organizations/{id}/history/` | Workspace history |

## Goals and Key Results

| Method | Endpoint | Purpose |
|---|---|---|
| GET/POST | `/goals/?organization={id}` | List/create goals |
| GET/PATCH/DELETE | `/goals/{id}/` | Retrieve/update/delete goal |
| POST | `/goals/{id}/restore/` | Restore soft-deleted goal |
| GET/POST | `/goals/{goal_id}/key-results/` | List/create KRs |
| GET/PATCH/DELETE | `/goals/{goal_id}/key-results/{id}/` | KR detail/update/delete |
| GET/POST | `/org/{slug}/goals/` | Slug-scoped goals |
| GET/PATCH/DELETE | `/org/{slug}/goals/{id}/` | Slug-scoped goal detail |

## Tasks

| Method | Endpoint | Purpose | Main Validation |
|---|---|---|---|
| POST | `/tasks/create/` | Create standalone task | org required, related users must be active members |
| POST | `/goals/{goal_id}/tasks/create/` | Create task linked to goal | same as above |
| GET | `/organizations/{org_id}/tasks/` | List visible tasks | membership/visibility |
| GET/PATCH/PUT | `/tasks/{task_id}/` | Task detail/update | permissions, visibility, scheduling recalculation |
| DELETE | `/tasks/{task_id}/` | Hard delete | permissions |
| PATCH | `/tasks/{task_id}/update-status/` | Quick status/assignee update | assignment permission |
| DELETE | `/tasks/{task_id}/soft-delete/` | Soft delete | permissions |
| GET | `/organizations/{org_id}/trash/` | Trash list | permissions |
| POST | `/tasks/{task_id}/restore/` | Restore task | permissions |
| GET/POST | `/tasks/{task_id}/comments/`, `/comments/{id}/reply/` | Comment threads | visibility |
| POST | `/tasks/{task_id}/attachments/upload/` | Upload attachment | multipart |
| POST | `/organizations/{org_id}/tasks/bulk-update/` | Bulk update | permission-dependent |
| POST | `/quick-assign-task/` | Quick assign | member validation |
| GET | `/organizations/{org_id}/tasks/filter/` | Filtered tasks | query filters |
| GET | `/organizations/{org_id}/tasks/kanban/` | Ticket kanban | visible tasks/tickets |
| PATCH | `/tasks/tickets/{ticket_id}/update-status/` | Update ticket status/time | ticket status choices |
| POST | `/tasks/{task_id}/extension-request/` | Request extension | reason/proposed date |
| GET | `/organizations/{org_id}/extension-requests/` | List extension requests | admin/owner scope |
| PATCH | `/extension-requests/{id}/review/` | Approve/reject/modify extension | reviewer permissions |
| POST | `/tasks/{task_id}/feedback/` | Create feedback | one per user per task |
| POST | `/tasks/{task_id}/submit/` | Submit proof | multipart/form data |
| PATCH | `/tasks/{task_id}/change-assignee/` | Admin/creator override | target member required |

## Scheduler APIs

| Method | Endpoint | Purpose | Request | Response |
|---|---|---|---|---|
| POST | `/organizations/{org_id}/tasks/manual-schedule/` | Schedule one member or all members | optional `user_id` | scheduled task list |
| POST | `/organizations/{org_id}/tasks/schedule-preview/` | Preview next available slot | `assignee`, `estimated_hours`, optional `task_id`, `start_search_from` | `planned_start`, `planned_end`, `segments`, message |
| POST | `/organizations/{slug}/tasks/run_scheduler/` | Run scheduler for queued tasks | none | scheduled count |
| POST | `/organizations/{slug}/tasks/import_csv/` | Import tasks from CSV | `file` | created/scheduled/queued counts |

## Notifications

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/notifications/` | List user notifications |
| POST | `/notifications/{id}/mark-read/` | Mark one read |
| POST | `/notifications/mark-all-read/` | Mark all read |
| DELETE | `/notifications/{id}/clear/` | Delete one |
| DELETE | `/notifications/clear-all/` | Delete all |
| POST | `/notifications/webpush-subscribe/` | Save web push subscription |

## Chat

| Method | Endpoint | Purpose |
|---|---|---|
| GET/POST | `/org/{slug}/chat/rooms/` | List/create rooms |
| POST | `/org/{slug}/chat/rooms/direct/` | Create/direct room |
| POST | `/org/{slug}/chat/rooms/group/` | Create group |
| GET/PATCH/DELETE | `/org/{slug}/chat/rooms/{id}/` | Room detail |
| GET/POST | `/org/{slug}/chat/rooms/{room_id}/messages/` | List/send messages |
| GET/PATCH/DELETE | `/org/{slug}/chat/rooms/{room_id}/messages/{id}/` | Message detail |

WebSockets:

- `ws/chat/{org_id}/`
- `ws/notifications/`

## Templates, Imports, Notes, Dashboard

| Method | Endpoint | Purpose |
|---|---|---|
| GET/POST | `/org/{slug}/templates/` | Template list/create |
| GET/PUT/DELETE | `/org/{slug}/templates/{id}/` | Template detail |
| POST | `/org/{slug}/templates/{id}/apply/` | Apply template |
| POST | `/org/{slug}/templates/{id}/create_and_apply/` | Create goal from template |
| POST | `/org/{slug}/templates/import-file/` | Import template file |
| POST | `/org/{slug}/import-csv/` | Bulk import CSV |
| GET/POST | `/notes/` | Notes |
| GET/PATCH/DELETE | `/notes/{id}/` | Note detail |
| GET | `/dashboard/available-apps/` | Available apps |
| GET/POST/PATCH/DELETE | `/dashboard/workspace-apps/` | Workspace apps |
| GET | `/analytics/org/{org_id}/` | Dashboard analytics |

## Frontend-Integrated but Missing/Commented Backend Routes

The frontend wrapper exposes these routes, but the backend URL file has corresponding routes commented or absent:

- `/organizations/{org_id}/tasks/smart-suggest/`
- `/organizations/{org_id}/tasks/check-free-members/`
- `/organizations/{org_id}/tasks/assign-suggested/`
- `/organizations/{org_id}/tasks/bulk-schedule/`
- `/organizations/{org_id}/tasks/preview-schedule/`
- `/organizations/{org_id}/tasks/apply-schedule/`
