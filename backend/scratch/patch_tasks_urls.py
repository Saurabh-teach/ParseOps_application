import re

with open('c:/Users/saura/ParseOps/backend/tasks/urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = "    CreateTaskFeedbackView\n)"
replacement = "    CreateTaskFeedbackView, TaskSubmissionView\n)"
content = content.replace(target, replacement)

target2 = "path('tasks/<uuid:task_id>/feedback/', CreateTaskFeedbackView.as_view(), name='task-feedback'),"
replacement2 = "path('tasks/<uuid:task_id>/feedback/', CreateTaskFeedbackView.as_view(), name='task-feedback'),\n    path('tasks/<uuid:task_id>/submit/', TaskSubmissionView.as_view(), name='task-submit'),"
content = content.replace(target2, replacement2)

with open('c:/Users/saura/ParseOps/backend/tasks/urls.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("tasks/urls.py patched")
