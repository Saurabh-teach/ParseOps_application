import re

with open('c:/Users/saura/ParseOps/frontend/src/api.js', 'r', encoding='utf-8') as f:
    content = f.read()

target = """export const updateTaskTicketStatus = async (ticketId, status) => {
  const response = await api.patch(`/tasks/tickets/${ticketId}/update-status/`, { status });"""

replacement = """export const updateTaskTicketStatus = async (ticketId, status, add_time_minutes = undefined) => {
  const payload = {};
  if (status !== undefined) payload.status = status;
  if (add_time_minutes !== undefined) payload.add_time_minutes = add_time_minutes;
  const response = await api.patch(`/tasks/tickets/${ticketId}/update-status/`, payload);"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/frontend/src/api.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("api.js patched to support add_time_minutes")
