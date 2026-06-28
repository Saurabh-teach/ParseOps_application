import re

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

target1 = """                                        onChange={async (e) => {
                                          try {
                                            await handleUpdateTicketStatus(ticket.id, e.target.value);
                                            const updatedTickets = activeTask.tickets.map(t => t.id === ticket.id ? { ...t, status: e.target.value } : t);
                                            setActiveTask({ ...activeTask, tickets: updatedTickets });
                                          } catch (err) {
                                            console.error(err);
                                          }
                                        }}"""

replacement1 = """                                        onChange={async (e) => {
                                          if (e.target.value === 'done') {
                                            setSubmissionModalConfig({ isOpen: true, ticketId: ticket.id, taskId: activeTask.id, taskTitle: activeTask.title });
                                            // Reset dropdown visually by doing nothing since value is still ticket.status
                                            return;
                                          }
                                          try {
                                            await handleUpdateTicketStatus(ticket.id, e.target.value);
                                            const updatedTask = await getOrgTaskDetail(selectedOrg.slug, activeTask.id);
                                            setActiveTask(updatedTask);
                                            handleLoadTasks();
                                          } catch (err) {
                                            console.error(err);
                                          }
                                        }}"""

content = content.replace(target1, replacement1)

target2 = """                                        onChange={async (e) => {
                                        try {
                                          await handleUpdateTicketStatus(ticket.id, e.target.value);
                                          const updatedTickets = activeTask.tickets.map(t => t.id === ticket.id ? { ...t, status: e.target.value } : t);
                                          setActiveTask({ ...activeTask, tickets: updatedTickets });
                                        } catch (err) {
                                          console.error(err);
                                        }
                                      }}"""

replacement2 = """                                        onChange={async (e) => {
                                        if (e.target.value === 'done') {
                                          setSubmissionModalConfig({ isOpen: true, ticketId: ticket.id, taskId: activeTask.id, taskTitle: activeTask.title });
                                          return;
                                        }
                                        try {
                                          await handleUpdateTicketStatus(ticket.id, e.target.value);
                                          const updatedTask = await getOrgTaskDetail(selectedOrg.slug, activeTask.id);
                                          setActiveTask(updatedTask);
                                          handleLoadTasks();
                                        } catch (err) {
                                          console.error(err);
                                        }
                                      }}"""

content = content.replace(target2, replacement2)

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("App.jsx patched for 'done' intercept")
