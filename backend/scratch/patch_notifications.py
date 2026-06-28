with open('c:/Users/saura/ParseOps/backend/notifications/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_code = """        ('task_overdue', 'Task Overdue'),
        ('task_completed', 'Task Completed'),
    )"""

new_code = """        ('task_overdue', 'Task Overdue'),
        ('task_completed', 'Task Completed'),
        ('chat_message', 'New Chat Message'),
        ('chat_mention', 'Mentioned in Chat'),
        ('chat_group_added', 'Added to Group Chat'),
    )"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('c:/Users/saura/ParseOps/backend/notifications/models.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched notifications/models.py")
else:
    print("Not found")
