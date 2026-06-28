import re

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("Q(end_date__gte=s_dt)", "Q(due_date__gte=s_dt)")
content = content.replace("end = g.end_date.isoformat() if g.end_date else start", "end = g.due_date.isoformat() if g.due_date else start")

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("organizations/views.py patched for end_date -> due_date")
