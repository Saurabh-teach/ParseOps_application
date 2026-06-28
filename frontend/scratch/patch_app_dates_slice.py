import re

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace activeTask.start_date || '' with (activeTask.start_date ? activeTask.start_date.substring(0, 10) : '')
content = content.replace("value={activeTask.start_date || ''}", "value={activeTask.start_date ? activeTask.start_date.substring(0, 10) : ''}")
content = content.replace("value={activeTask.due_date || ''}", "value={activeTask.due_date ? activeTask.due_date.substring(0, 10) : ''}")

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("App.jsx updated with substring for date inputs.")
