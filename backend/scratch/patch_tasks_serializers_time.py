import re

with open('c:/Users/saura/ParseOps/backend/tasks/serializers.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = "        fields = ['id', 'task', 'task_details', 'assignee', 'assignee_details', 'status', 'created_at', 'updated_at']"
replacement = "        fields = ['id', 'task', 'task_details', 'assignee', 'assignee_details', 'status', 'time_spent_minutes', 'created_at', 'updated_at']"

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/backend/tasks/serializers.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Added time_spent_minutes to TaskTicketSerializer fields")
