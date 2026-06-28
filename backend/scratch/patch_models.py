with open('c:/Users/saura/ParseOps/backend/goals/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("default='organization'", "default='specific'")

with open('c:/Users/saura/ParseOps/backend/goals/models.py', 'w', encoding='utf-8') as f:
    f.write(content)

with open('c:/Users/saura/ParseOps/backend/tasks/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("default='organization'", "default='specific'")

with open('c:/Users/saura/ParseOps/backend/tasks/models.py', 'w', encoding='utf-8') as f:
    f.write(content)
