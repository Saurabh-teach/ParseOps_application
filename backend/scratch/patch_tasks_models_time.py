import re

with open('c:/Users/saura/ParseOps/backend/tasks/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = "    status = models.CharField(max_length=20, choices=Task.STATUS_CHOICES, default='todo')"
replacement = "    status = models.CharField(max_length=20, choices=Task.STATUS_CHOICES, default='todo')\n    time_spent_minutes = models.PositiveIntegerField(default=0, help_text=\"Total minutes spent on this ticket\")"

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/backend/tasks/models.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Added time_spent_minutes to TaskTicket model")
