# 11 Sequence Diagrams

## User Login

```mermaid
sequenceDiagram
  participant U as User
  participant F as React
  participant A as Auth API
  participant O as OTP Service
  participant D as Database
  U->>F: Enter email/password
  F->>A: POST /users/login/
  A->>D: Validate user/password
  A->>O: Create/send OTP
  A-->>F: OTP required
  U->>F: Enter OTP
  F->>A: POST /users/verify-login-otp/
  A->>D: Validate OTP
  A-->>F: access/refresh tokens
  F->>F: Store tokens in sessionStorage
```

## Create Task

```mermaid
sequenceDiagram
  participant U as User
  participant F as React
  participant T as Task API
  participant S as Scheduler
  participant D as Database
  U->>F: Submit task form
  F->>T: POST /tasks/create/
  T->>D: Validate org/members/permissions
  T->>D: Save Task
  T->>S: schedule_tasks_for_assignee()
  S->>D: Read existing planned tasks/leaves/schedule
  S->>D: Save planned_start/planned_end or queue
  T-->>F: Task + scheduled_details
```

## Scheduler

```mermaid
sequenceDiagram
  participant API as API/Celery
  participant S as SchedulerService
  participant C as Calendar Service
  participant D as Database
  API->>S: schedule_tasks_for_assignee(user, org)
  S->>D: Lock queued/future auto tasks
  S->>D: Load org/user schedule and leaves
  loop each task
    S->>C: get_working_intervals(day)
    S->>D: get busy slots
    S->>S: subtract occupied intervals
    alt Capacity found
      S->>D: Mark SCHEDULED + store segments
    else No capacity
      S->>D: Mark QUEUED + queue position
    end
  end
```

## Queue Promotion

```mermaid
sequenceDiagram
  participant Trigger as Manual/Celery/Edit
  participant S as Scheduler
  participant N as Notification Service
  participant D as Database
  Trigger->>S: schedule_tasks_for_assignee()
  S->>D: Fetch QUEUED tasks
  S->>S: Find capacity
  alt Was queued and now scheduled
    S->>D: Save scheduled fields
    S->>N: send task_scheduled_from_queue
  else Still no capacity
    S->>D: Keep queued
  end
```

## Task Edit

```mermaid
sequenceDiagram
  participant F as React
  participant T as Task API
  participant S as Scheduler
  participant D as Database
  F->>T: PATCH /tasks/{id}/
  T->>D: Load and permission-check task
  T->>D: Save serializer fields
  alt start/duration/end changed
    T->>S: Recalculate dependent fields
    T->>D: Save planned/duration fields
  end
  T->>D: on_commit cascade reschedule
  D-->>T: Commit
  T-->>F: Updated task
```

## Task Completion

```mermaid
sequenceDiagram
  participant F as React
  participant T as Ticket API
  participant D as Database
  participant N as Notifications
  F->>T: PATCH ticket status done
  T->>D: Save TaskTicket
  D->>D: Signal recalculates master Task status
  D->>N: Completion/update notifications
  T-->>F: Updated ticket/task status
```

## Working Schedule Update

```mermaid
sequenceDiagram
  participant F as React
  participant U as User Profile API
  participant D as Database
  participant S as Scheduler
  F->>U: PATCH /users/profile/
  U->>D: Validate and save UserWorkingSchedule
  D->>S: post_save/on_commit reschedule future tasks
  S->>D: Reflow future tasks
  U-->>F: Updated profile
```

# 12 Flowcharts

## Scheduler Flow

```mermaid
flowchart TD
  A["Start scheduler for assignee"] --> B["Load queued and future auto-scheduled tasks"]
  B --> C["Sort by existing schedule, priority, impact, risk, due date, created date"]
  C --> D["For each task"]
  D --> E["Load org/user schedule and leave dates"]
  E --> F["Build working intervals"]
  F --> G["Subtract occupied intervals"]
  G --> H{"Enough minutes within scan window?"}
  H -- Yes --> I["Set SCHEDULED, planned_start/end, segment JSON"]
  H -- No --> J["Set QUEUED, clear planned dates, queue_position"]
  I --> K{"More tasks?"}
  J --> K
  K -- Yes --> D
  K -- No --> L["Return scheduled tasks"]
```

## Gap Filling

```mermaid
flowchart TD
  A["Candidate working day"] --> B["Get work intervals minus breaks"]
  B --> C["Get existing planned task intervals"]
  C --> D["Subtract busy from working"]
  D --> E["Scan free intervals from anchor"]
  E --> F["Allocate segment minutes"]
  F --> G{"Remaining duration?"}
  G -- Yes --> H["Advance to next free interval/day"]
  G -- No --> I["Return segment list"]
  H --> E
```

## Rescheduling

```mermaid
flowchart TD
  A["Task/date/schedule/leave changes"] --> B["Commit transaction"]
  B --> C["Run scheduler after commit"]
  C --> D["Determine affected assignee/org"]
  D --> E["Repack future scheduled and queued tasks"]
  E --> F["Preserve order and fill gaps"]
  F --> G["Save scheduled or queued results"]
```

## Queue

```mermaid
flowchart TD
  A["Task requires scheduling"] --> B{"Assignee exists?"}
  B -- No --> C["QUEUED: No assignee"]
  B -- Yes --> D["Find available segments"]
  D --> E{"Capacity found?"}
  E -- Yes --> F["SCHEDULED"]
  E -- No --> G["QUEUED: Waiting For Capacity"]
  G --> H["Manual/Celery/edit trigger reruns scheduler"]
  H --> D
```
