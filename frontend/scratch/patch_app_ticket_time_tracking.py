import re

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

target = """                        {activeTask.tickets && activeTask.tickets.length > 0 && (
                          <div className="task-detail-meta-group">
                            <h4 className="task-detail-meta-label">Assignee Tickets</h4>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', background: '#f8fafc', padding: '0.6rem', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                              {activeTask.tickets.map(ticket => {"""

replacement = """                        {activeTask.tickets && activeTask.tickets.length > 0 && (
                          <div className="task-detail-meta-group">
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                              <h4 className="task-detail-meta-label" style={{ margin: 0 }}>Assignee Tickets</h4>
                              <span style={{ fontSize: '0.7rem', fontWeight: 600, color: '#4f46e5', background: '#e0e7ff', padding: '0.15rem 0.4rem', borderRadius: '4px' }}>
                                Total Time Spent: {(activeTask.tickets.reduce((acc, t) => acc + (t.time_spent_minutes || 0), 0) / 60).toFixed(1)} hrs
                              </span>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', background: '#f8fafc', padding: '0.6rem', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                              {activeTask.tickets.map(ticket => {
                                const totalTaskEstMins = (parseFloat(activeTask.estimated_hours) || 0) * 60 + (parseInt(activeTask.estimated_minutes) || 0);
                                const estMins = totalTaskEstMins / Math.max(1, activeTask.tickets.length);
                                const spentMins = ticket.time_spent_minutes || 0;
                                const remainingMins = Math.max(0, estMins - spentMins);
                                const progress = estMins > 0 ? Math.min(100, Math.round((spentMins / estMins) * 100)) : 0;"""

content = content.replace(target, replacement)

target2 = """                                      <span style={{ fontWeight: 600, color: '#334155' }}>
                                        {ticket.assignee_name} {isMyTicket && <span style={{ color: '#6366f1', fontSize: '0.65rem', fontWeight: 'normal' }}>(You)</span>}
                                      </span>
                                    </div>
                                    {canModifyThisTicket ? (
                                      <select
                                        className="task-form-select"
                                        style={{ padding: '0.3rem 0.4rem', background: 'white', fontSize: '0.72rem', marginTop: '0.1rem' }}
                                        value={ticket.status}
                                        onChange={async (e) => {"""

replacement2 = """                                      <span style={{ fontWeight: 600, color: '#334155' }}>
                                        {ticket.assignee_name} {isMyTicket && <span style={{ color: '#6366f1', fontSize: '0.65rem', fontWeight: 'normal' }}>(You)</span>}
                                      </span>
                                    </div>
                                    
                                    <div style={{ fontSize: '0.7rem', color: '#64748b', display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.25rem', marginTop: '0.2rem', marginBottom: '0.2rem' }}>
                                      <div><span style={{fontWeight: 600}}>Time Spent:</span> {(spentMins / 60).toFixed(1)} hrs</div>
                                      <div><span style={{fontWeight: 600}}>Remaining:</span> {(remainingMins / 60).toFixed(1)} hrs</div>
                                      <div><span style={{fontWeight: 600}}>Progress:</span> {progress}%</div>
                                    </div>
                                    <div style={{ width: '100%', background: '#e2e8f0', height: '4px', borderRadius: '2px', marginBottom: '0.3rem' }}>
                                      <div style={{ width: `${progress}%`, background: progress >= 100 ? '#10b981' : '#6366f1', height: '100%', borderRadius: '2px' }}></div>
                                    </div>

                                    {canModifyThisTicket ? (
                                      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                                        <select
                                          className="task-form-select"
                                          style={{ padding: '0.3rem 0.4rem', background: 'white', fontSize: '0.72rem', flex: 1 }}
                                          value={ticket.status}
                                          onChange={async (e) => {"""

content = content.replace(target2, replacement2)

target3 = """                                        <option value="in_review">In Review</option>
                                        <option value="testing">Testing</option>
                                        <option value="done">Done</option>
                                      </select>
                                    ) : ("""

replacement3 = """                                        <option value="in_review">In Review</option>
                                        <option value="testing">Testing</option>
                                        <option value="done">Done</option>
                                      </select>
                                      <button 
                                        style={{ padding: '0.3rem 0.5rem', fontSize: '0.7rem', background: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '4px', cursor: 'pointer' }}
                                        onClick={async () => {
                                          const mins = window.prompt("Enter time spent in minutes (e.g. 30, 60, 90):", "30");
                                          if (mins && !isNaN(parseInt(mins))) {
                                            try {
                                              await api.patch(`/organizations/${selectedOrg.slug}/tasks/tickets/${ticket.id}/update_status/`, { add_time_minutes: parseInt(mins) });
                                              const updatedTask = await getOrgTaskDetail(selectedOrg.slug, activeTask.id);
                                              setActiveTask(updatedTask);
                                              handleLoadTasks();
                                            } catch (err) {
                                              console.error(err);
                                              alert('Failed to log time');
                                            }
                                          }
                                        }}
                                      >
                                        + Log Time
                                      </button>
                                      </div>
                                    ) : ("""

content = content.replace(target3, replacement3)

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("App.jsx patched for Assignee Tickets Time Tracking")
