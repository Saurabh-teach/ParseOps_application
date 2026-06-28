import re

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

target = """                                            await api.patch(`/organizations/${selectedOrg.slug}/tasks/tickets/${ticket.id}/update_status/`, { add_time_minutes: parseInt(mins) });"""

replacement = """                                            await updateTaskTicketStatus(ticket.id, undefined, parseInt(mins));"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("App.jsx updated to use updateTaskTicketStatus instead of api.patch")
