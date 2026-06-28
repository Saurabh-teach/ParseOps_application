# 14 Current Problems

## Architecture Issues

- `App.jsx` centralizes too many workflows and state domains.
- Backend views contain significant business logic that could be moved into services.
- Scratch, recovery, debug, and patch files are present in repository root, backend, and frontend.
- Local SQLite database and debug output files are present in the worktree.
- Settings include development/security-sensitive configuration.

## Duplicate Logic

- Scheduler logic exists in `tasks/services/calendar.py`, `tasks/services/scheduler.py`, `tasks/schedule_utils.py`, frontend `scheduleUtils.js`, and `ScheduleTasksModal.jsx`.
- Task assignment has single `assignee` but backward-compatible `assignees` API fields.
- Goal/task organization-scoped APIs exist both ID-based and slug-based.

## Scheduler Problems

- Missing class method for `SchedulerService.reschedule_subsequent_tasks`.
- Manual task pinning during create is unclear because auto-scheduling still runs.
- Queue position is not consistently assigned in all queued paths.
- `schedule_reason` mixes human-readable text and JSON segment data.
- Scheduler status includes `COMPLETED`, but task completion mainly uses task status `done`.
- Some excluded statuses are not valid task choices.
- Concurrent scheduler triggers can race for the same assignee.
- Preview writes to an absolute debug file path.
- User schedule object is not always passed correctly to calendar functions.

## Frontend Problems

- Frontend API wrappers reference missing/commented backend routes.
- Frontend scheduling calculations can diverge from backend rules.
- Session storage token storage is vulnerable to XSS exposure.
- No formal client-side route system is visible.
- No centralized data fetching/caching layer.
- Large component complexity increases regression risk.

## Backend Problems

- Hard-coded secret key, SMTP credentials, DEBUG, permissive CORS, and local host assumptions.
- `MEDIA_ROOT=BASE_DIR` can mix uploaded media with source files.
- Requirements file appears incomplete compared with imports.
- Absolute file paths in code reduce portability.
- Debug and generated artifacts are mixed into application tree.

## Performance Problems

- Scheduling may scan many tasks/users every 30 minutes.
- Notifications and dashboard polling can produce repeated queries.
- Serializer method fields can trigger N+1 queries if querysets are not preloaded.
- Chat and notifications need pagination/backpressure review.

## Database Problems

- PostgreSQL is configured, but SQLite database artifact exists.
- Some constraints are only application-level, not database-level.
- Segment data should be normalized or stored in JSON field instead of `schedule_reason`.
- Role/permission JSON lacks schema constraints.

## API Problems

- Some endpoints are implemented as APIViews with inconsistent response shapes.
- Route naming mixes IDs and slugs.
- Error response shape varies among `error`, `detail`, serializer errors, and messages.
- Schema coverage is incomplete.

## Race Conditions

- Manual scheduler, Celery scheduler, task update, leave update, and working-schedule update can overlap.
- Ticket timer relies on `updated_at` and pre-save elapsed calculations, which can be affected by unrelated ticket saves.
- Queue promotion notifications may duplicate if concurrent runs both see queued state.

## Timezone Issues

- Backend timezone is UTC, organizations have their own timezone, frontend converts locally.
- Preview returns localized ISO strings, while database stores UTC.
- Overnight shifts and DST transitions need explicit tests.

## Duration Calculation Problems

- `estimated_hours` and `estimated_minutes` are synchronized in serializer but can drift through manual edits or direct DB changes.
- Frontend assumes 8-hour plus breaks in one function and 10-hour fixed shift in another.
- Legacy `shift_datetime_working_minutes()` appears to compute then return `add_working_time(dt, 0, user)`, losing the computed shifted value.

## Gap Filling Issues

- Gap filling is implemented, but product rules do not define whether segmenting across multiple intervals is acceptable for all task types.
- Existing scheduled tasks and manual pinned tasks need clearer precedence.
- Additional breaks exist at organization level but not consistently in frontend preview logic.

## Queue Problems

- Queue ordering is implicit and not exposed as a first-class product rule.
- Queue positions may become stale after task edits/deletions.
- No dedicated queue model/history exists.
