import re

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

target = """                                        onChange={async (e) => {
                                          try {
                                            await handleUpdateTicketStatus(ticket.id, e.target.value);
                                            const updatedTickets = activeTask.tickets.map(t => t.id === ticket.id ? { ...t, status: e.target.value } : t);
                                            setActiveTask({ ...activeTask, tickets: updatedTickets });
                                          } catch (err) {
                                            console.error(err);
                                          }
                                        }}"""

replacement = """                                        onChange={async (e) => {
                                          try {
                                            await handleUpdateTicketStatus(ticket.id, e.target.value);
                                            // Refetch the full task details to pick up any parent status changes
                                            const updatedTask = await getOrgTaskDetail(selectedOrg.slug, activeTask.id);
                                            setActiveTask(updatedTask);
                                            handleLoadTasks();
                                          } catch (err) {
                                            console.error(err);
                                          }
                                        }}"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("App.jsx patched to refetch active task on ticket update")
