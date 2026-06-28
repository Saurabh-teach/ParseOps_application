# 3 User Roles

## Identified Roles

| Role | Scope | Responsibilities |
|---|---|---|
| Anonymous | Public/auth endpoints | Register, login, verify OTP, reset password, accept invitation where token-based |
| Authenticated User | Global | Manage profile, view joined workspaces, request joins, manage own leaves/notes |
| Organization Member | Organization | View accessible tasks/goals, create allowed work, manage assigned work, request extensions, submit task proof |
| Organization Admin | Organization | Manage members/tasks/goals, approve requests, view broader private work, run scheduling |
| Organization Owner | Organization | Full organization management, owner protection, member/role/invitation control |
| Task Creator | Task | Edit/delete created tasks depending on permission checks |
| Goal Owner | Goal | Manage goal and associated tasks depending on permission checks |
| Assignee | Task/Ticket | Execute task ticket, update status, submit proof, request extension |

## Access Matrix

| Capability | Anonymous | Member | Admin | Owner |
|---|---:|---:|---:|---:|
| Register/login | Yes | Yes | Yes | Yes |
| Create organization | No | Yes | Yes | Yes |
| Invite members | No | No/permission-dependent | Yes | Yes |
| Approve join requests | No | No | Yes | Yes |
| Remove members | No | No | Yes | Yes |
| Change member role | No | No | Yes | Yes |
| View all org tasks | No | No | Yes | Yes |
| View own/visible tasks | No | Yes | Yes | Yes |
| Create task | No | Yes, subject to permissions | Yes | Yes |
| Assign task to owner/admin | No | No | Yes | Yes |
| Run manual scheduler | No | Own tasks only | Yes | Yes |
| Manage key results | No | Permission-dependent | Yes | Yes |
| Approve leave/extension | No | No | Yes | Yes |

## Permission Notes

- Organization membership must be active for most organization-scoped operations.
- Owners/admins override task visibility and can see all tasks in an organization.
- Members see organization-wide tasks and tasks where they are creator, assignee, watcher, explicit visible user, or shared viewer.
- A regular member is explicitly blocked from assigning tasks to admins or owners during task creation.
- Organization membership prevents deleting/demoting the last active owner.
- Custom permissions exist as JSON on membership and are checked through `core.permissions`.
