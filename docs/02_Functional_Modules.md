# 2 Functional Modules

## Authentication

Supports email-based registration, OTP verification, login, login OTP verification, JWT refresh, logout, password reset, email change verification, Microsoft OAuth views, and SAML views. The custom user model removes username and uses unique email as the login identifier.

## Organizations

Organizations are workspaces with owner, slug, logo, description, active/public flags, onboarding status, scheduling configuration, timezone, and members. Membership roles are `owner`, `admin`, and `member`. The module supports join requests, invitations, pending invitations, member listing, member removal/restoration, role changes, custom permissions, calendar events, workspace history, and invitation acceptance/decline.

## Goals

Goals belong to organizations and support owner, creator, progress, status, priority, dates, visibility, sharing, assignees, parent goals, dependencies, templates, and external sharing flags. Key results calculate progress; if no key results exist, goal progress falls back to linked task completion.

## Tasks

Tasks belong to organizations and optionally goals. A task has a single canonical `assignee` field, while serializers preserve backward-compatible `assignees` input and output. Tasks support issue type, status, priority, due dates/times, estimated and actual duration, reminders, soft deletion, visibility, sharing, extensions, scoring fields, tickets, comments, attachments, feedback, submissions, and scheduling fields.

## Scheduler

The scheduler places assigned tasks into available working intervals. It considers organization working days, timezone, organization breaks, additional breaks, approved leaves, and user working schedules. Tasks that cannot fit within the scan window are queued with `schedule_status='QUEUED'` and a queue position/reason.

## Queue

Queued tasks are tasks without a found scheduling slot. Manual scheduler and automatic scheduler runs can move queued tasks into scheduled slots. Queue ordering is based on scheduled status, planned start, priority, impact, risk, due date, and created date.

## Notifications

Notifications are stored per user and organization. Types cover organization join/invite events, goals, tasks, schedule changes, task queue transitions, extensions, and chat. The frontend polls notifications and also includes websocket/push-related support.

## User Profile and Working Schedule

Profiles include identity, contact, job fields, scoring fields, photo, education, and nested working schedule. User working schedule stores work start/end, lunch, and tea break times. Saving user schedule can trigger future task rescheduling.

## Leave Management

Users can submit leave requests by organization and leave type. Owners/admins can approve/reject/cancel where permitted. Leave balances are tracked by user, organization, and leave type. Approved leaves affect availability scoring and scheduler capacity.

## Calendar

The frontend includes `CalendarView` and organization calendar events. Calendar events are inferred from goals, tasks, leaves, and scheduled/planned dates. Scheduler outputs include planned start/end and segments that can feed calendar displays.

## Dashboard and Analytics

Dashboard analytics expose personal/team task metrics, filter controls, goal/member/priorities/date filtering, charts, and navigation into task views. Workspace apps allow organizations to enable dashboard features.

## Chat

Chat supports direct, group, goal, and task rooms. Goal/task rooms are created by signals. Chat includes participants, messages, replies, attachments, reactions, URL preview support, typing, read state, and websocket routing.

## Templates and Imports

Project templates include folders and typed items. Templates can be created, imported, applied to goals, and used to generate goal artifacts. CSV import paths exist for bulk goals/templates and task imports.

## Notes

Notes are user-owned and optionally organization-scoped. Notes are soft-active through `is_active`, ordered by last update.
