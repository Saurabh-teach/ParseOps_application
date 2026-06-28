\*\*Full Requirements Document:\*\*



ParseOps – Intelligent Dynamic Task Scheduling System (Full Requirements)



Goal: Build a smart, per-user, fully dynamic task scheduler that feels automatic and professional.



1\. Per-User Working Schedule (Core Foundation)

&#x20;  - Every user can set their own working schedule independently.

&#x20;  - Fields: Work Start Time, Work End Time (custom), Lunch Break (Start + End), Tea Break (Start + End).

&#x20;  - Default: 10:00 AM – 7:00 PM, Lunch 1-2 PM, Tea 5-5:30 PM.

&#x20;  - All data must be saved permanently per user in the database.

&#x20;  - Changes must persist after refresh, logout, login, server restart.

&#x20;  - Any change in schedule must trigger rescheduling for that user only.



2\. Dynamic Task Scheduling

&#x20;  - When creating a task, use the assignee’s personal schedule.

&#x20;  - Find the earliest continuous free gap that fits the full estimated duration.

&#x20;  - Respect working hours, breaks, existing tasks, and holidays.



3\. Dynamic Time Calculation \& Editing

&#x20;  - Change Estimated Hours/Minutes → auto update Scheduled End.

&#x20;  - Change Scheduled Start → auto update Scheduled End.

&#x20;  - Duration must always equal actual working minutes.



4\. Cascade Rescheduling (Most Important)

&#x20;  - When any task’s time or duration is changed, automatically shift all subsequent tasks of the same user.

&#x20;  - Maintain correct chaining with no overlaps.



5\. Break \& Schedule Change Handling

&#x20;  - When user changes work time or breaks in Profile → automatically reschedule all their tasks.



6\. Special Cases

&#x20;  - All 8 cases mentioned in the document must be handled correctly.



7\. Queue \& 7-Day Rule

&#x20;  - If no slot in 7 working days → move to Queue.



8\. Consistency

&#x20;  - Schedule Preview = Database = Task List = Task Details.



\*\*Instructions for AI:\*\*



\*\*Task:\*\*



You are an expert Django backend developer.



Read the full requirements document above.



Fix the following issues in the scheduling system:



1\. When Estimated Hours is changed, Scheduled End time must update correctly (exact duration).

2\. When Scheduled Start time is changed, Scheduled End time must update correctly.

3\. Cascade rescheduling: When one task is changed, all subsequent tasks of the same user must shift automatically with correct dates and times.

4\. Saving changes in Task Details must persist properly in the database.

5\. Respect per-user working schedule, lunch, and tea breaks.



\*\*Rules:\*\*

\- Do NOT rewrite the entire application.

\- Only enhance SchedulerService and Task update logic.

\- Keep existing code style and architecture.

\- Add clear comments.



Provide the full updated code for SchedulerService and any other changed files.

