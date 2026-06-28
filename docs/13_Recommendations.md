# 15 Recommended Improvements

## Production Hardening

- Move secrets, email credentials, VAPID keys, DB settings, and CORS origins to environment variables.
- Set `DEBUG=False` outside development.
- Configure `ALLOWED_HOSTS`.
- Move `MEDIA_ROOT` outside source tree.
- Remove local databases, debug logs, recovery artifacts, scratch scripts, and patch scripts from production repository.
- Expand `requirements.txt` to include all backend dependencies.

## Scheduler Improvements

- Consolidate scheduling into one backend source of truth.
- Remove or clearly deprecate `tasks/schedule_utils.py` once migration is complete.
- Add a dedicated `TaskScheduleSegment` model or JSON field for segments.
- Keep `schedule_reason` as human-readable reason only.
- Define and enforce manual pin policy.
- Implement idempotent per-assignee scheduler locks to prevent concurrent runs.
- Add complete tests for overnight shifts, holidays/leaves, DST, gap filling, queues, and manual tasks.
- Fix missing `reschedule_subsequent_tasks` wrapper or remove it.
- Ensure user object, not membership object, is passed to calendar functions.

## API Improvements

- Standardize response envelopes and error shape.
- Remove or implement frontend-referenced missing routes.
- Prefer slug or UUID routing consistently per resource.
- Add complete OpenAPI examples for create/update/preview/scheduler endpoints.
- Add pagination to all potentially large lists.
- Add request IDs and structured logging.

## Frontend Improvements

- Split `App.jsx` by domain into route-level pages and hooks.
- Add React Router or equivalent route management.
- Introduce a data-fetching cache such as TanStack Query.
- Treat backend scheduler preview as authoritative; reduce frontend scheduling calculations to display-only helpers.
- Normalize API error display.
- Use secure cookie-based auth if deployment model allows it.

## Database Improvements

- Add database constraints for more invariants where feasible.
- Normalize queue/schedule history if auditability matters.
- Add indexes for frequent filters: organization/status/assignee/due date, notifications unread, chat room updated, leaves by user/date/status.
- Define JSON schemas for custom permissions and schedule segments.

## Business Rule Improvements

- Formalize queue ordering and manager overrides.
- Formalize group task handling around `required_assignees`.
- Add holiday calendars per organization.
- Define SLA/reminder rules.
- Define how task extensions affect schedule and due dates.
- Define whether paused/delayed tasks occupy schedule capacity.

## Testing Improvements

- Add unit tests for serializers and services.
- Add scheduler property-style tests for interval arithmetic.
- Add API tests for permissions and visibility.
- Add frontend integration tests for auth, task creation, schedule preview, queue, and calendar.
- Add race-condition tests around scheduler concurrency where possible.

## Observability Improvements

- Replace debug file writes with structured logging.
- Track scheduler run metadata: start/end time, assignee, org, scheduled count, queued count, errors.
- Add admin/reporting view for queued task reasons.
- Add notification delivery status for email/push/websocket.
