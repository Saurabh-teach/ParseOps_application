# 7 Frontend Documentation

## Frontend Architecture

The frontend is a Vite React SPA. It has a large central `App.jsx` handling routing-like view state, authentication state, organization selection, goals, tasks, profile, permissions, notes, calendar, notifications, and modals. Supporting components are used for dashboard, chat, templates, scheduler UI, queue, notifications, task extension/feedback, and calendar.

## Core Files

| File | Purpose |
|---|---|
| `src/main.jsx` | React app bootstrap |
| `src/App.jsx` | Main application shell and most workflows |
| `src/api.js` | Axios client, token handling, endpoint wrappers |
| `src/utils/scheduleUtils.js` | Frontend working-time calculations |
| `src/components/Dashboard.jsx` | Analytics dashboard |
| `src/components/CalendarView.jsx` | Calendar display |
| `src/components/ScheduleTasksModal.jsx` | Scheduling modal and local scheduling helpers |
| `src/components/PendingQueueView.jsx` | Queued task interface |
| `src/components/NotificationDropdown.jsx` | Notification list/actions |
| `src/components/Chat/*` | Chat layout, contextual chat, websocket hook |
| `src/components/Templates/TemplateManager.jsx` | Template builder/import/apply workflow |

## State Management

The app uses React local state through `useState`, `useEffect`, and refs. Session persistence uses `sessionStorage` for:

- access token
- refresh token
- selected tab/view hints
- `mustChangePassword`

There is no Redux, Zustand, React Query, or centralized cache. API responses are loaded into local component state.

## API Integration

`api.js` creates one Axios instance:

- base URL: `http://127.0.0.1:8000/api`
- timeout: 8 seconds
- request interceptor attaches `Authorization: Bearer {token}`
- response interceptor refreshes token on 401
- dispatches `workspace_access_lost` when membership access errors occur

## Main Pages / Views

The app uses state-driven views rather than formal React Router pages:

- Login / registration / OTP
- Workspace list and organization onboarding
- Dashboard overview
- Goals list/detail/create/edit
- Tasks list/detail/create/edit
- Task board/Kanban
- Pending queue
- Scheduler modal
- Calendar
- Members/permissions
- Invitations and join requests
- Workspace history
- Profile and working schedule
- Leave management
- Notifications
- Notes/notebook
- Chat/contextual chat
- Templates

## Forms and Validation

Frontend validation is mostly local required-field and UI-state validation. Backend remains authoritative for:

- user membership
- role/permission checks
- task visibility
- leave overlap/balance
- working schedule break duration
- scheduler capacity
- duplicate goal/task names

## Scheduler UI

Frontend scheduling support exists in three places:

- `scheduleUtils.js`: mirrors backend-style work-time calculations for bidirectional task edit fields.
- `ScheduleTasksModal.jsx`: local preview/gap helpers and manual scheduler invocation.
- Task create/edit flows in `App.jsx`: request schedule preview, show planned dates, and update schedule fields.

Frontend utility behavior:

- Work start defaults to 10:00.
- Work end is computed from profile or as 8 working hours plus breaks in `getWorkSchedule()`.
- `calcWorkEndTime()` separately assumes a fixed 10-hour shift.
- Weekends are skipped, but organization-specific `working_days`, `additional_breaks`, approved leaves, and org timezone are not fully represented in frontend calculations.

## Calendar

Calendar UI uses FullCalendar packages. It is expected to show planned tasks, goal dates, leave events, and organization-level events. The backend exposes `calendar-events` and task planned fields/segments.

## Chat

Chat components call slug-scoped chat APIs and use `useChatSocket` for websocket updates. The chat UI supports room fetching, message fetching, sending text/files, typing state, emoji picker, direct/group creation, contextual goal/task rooms, and attachments.

## Frontend Issues to Track

- `App.jsx` is very large and mixes many domains.
- Some API wrappers point to missing/commented backend endpoints.
- Frontend schedule calculation can diverge from backend organization/user scheduler.
- Local/session storage token handling has security limitations compared with httpOnly cookies.
- No dedicated query caching or request de-duplication.
- Several recovery/debug files exist beside source files and should not be part of production structure.
