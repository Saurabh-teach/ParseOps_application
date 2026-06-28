import re

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = "goal_query &= Q(owners=request.user)"
replacement = "goal_query &= (Q(owner=request.user) | Q(assignees=request.user))"

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("organizations/views.py patched for owner/assignees")
