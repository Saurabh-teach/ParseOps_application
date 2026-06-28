# 8 Backend Documentation

## Backend Architecture

The backend is a Django project with modular apps:

| App | Responsibility |
|---|---|
| `users` | Custom user, auth flows, profile, working schedule, leaves |
| `organizations` | Workspaces, memberships, invitations, join requests, role management |
| `goals` | Goals, key results, progress, goal chat signals |
| `tasks` | Task lifecycle, scheduler, tickets, comments, submissions, extensions |
| `notifications` | Notification persistence, websocket, web push |
| `chat` | Chat rooms, participants, messages, websocket |
| `dashboard` | Workspace app registry |
| `analytics` | Dashboard analytics |
| `notes` | User/org notes |
| `project_templates` | Templates, folder/item trees, imports |
| `core` | Shared permissions and pagination |

## Business Logic Layers

- View classes handle request validation, permission checks, and orchestration.
- Serializers perform field mapping, derived fields, and validation.
- Services are used for scheduling, analytics, templates, notifications, and chat previews.
- Signals create chat rooms, synchronize task tickets/statuses, update goal progress, send notifications, and trigger reschedules.

## Scheduling Flow

The scheduler service is transaction-aware and uses thread-local depth to reduce recursive signal-triggered reschedules. It performs `select_for_update()` when scheduling a user's tasks, sorts tasks by priority/order, finds free segments, stores planned windows, and emits notifications when queued tasks become scheduled.

## Celery Tasks

`tasks.celery_tasks.auto_schedule_all_users` runs every 30 minutes through Celery Beat. It iterates active organizations and active memberships, then calls `schedule_tasks_for_assignee()` for each user.

## Transactions

Scheduling and task creation/update flows use `transaction.atomic()` and `transaction.on_commit()` for deferred rescheduling. This is appropriate for avoiding scheduler work against uncommitted task state.

## Signals

Important signal responsibilities:

- Create default user working schedule after user creation.
- Trigger future task rescheduling after working schedule changes.
- Trigger future task rescheduling after approved/cancelled leave changes.
- Create goal chat rooms and sync participants.
- Create task chat rooms.
- Sync task tickets and task status.
- Create notifications for task/goal/comment/extension events.
- Update goal progress when tasks/KRs change.

## Background Jobs and Realtime

- Celery Beat schedules periodic auto-scheduling.
- Channels exposes chat and notification websocket routes.
- Web push subscription storage exists, with a send helper.
- SMTP configuration is present for email notifications and OTP/invitation flows.

## API Schema

`drf-spectacular` is configured at:

- `/api/schema/`
- Swagger/ReDoc routes in `config.urls.py`

Schema decorators are used on many task/user endpoints, but not every endpoint has complete request/response examples.

## Security Configuration Observations

The current settings include development defaults:

- `DEBUG=True`
- empty `ALLOWED_HOSTS`
- `CORS_ALLOW_ALL_ORIGINS=True`
- hard-coded Django secret key
- hard-coded SMTP credentials
- VAPID key material in settings/repo context
- `MEDIA_ROOT=BASE_DIR`

These should be changed before production.
