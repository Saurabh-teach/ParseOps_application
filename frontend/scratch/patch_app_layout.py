import re

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Define the exact chunk to replace
target = """                        <div className="task-form-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
                          <div className="task-form-group">
                            <label className="task-form-label">Start Date</label>
                            <input
                              type="date"
                              className="task-form-input"
                              value={newTaskData.start_date || ''}
                              onChange={(e) => setNewTaskData({...newTaskData, start_date: e.target.value})}
                            />
                          </div>
                          <div className="task-form-group">
                            <label className="task-form-label">Due Date (End Date)</label>
                            <input
                              type="date"
                              className="task-form-input"
                              value={newTaskData.due_date || ''}
                              onChange={(e) => setNewTaskData({...newTaskData, due_date: e.target.value})}
                            />
                          </div>
                          <div className="task-form-group">
                            <label className="task-form-label">Due Time</label>
                            <input
                              type="time"
                              className="task-form-input"
                              value={newTaskData.due_time || ''}
                              onChange={(e) => setNewTaskData({...newTaskData, due_time: e.target.value})}
                            />
                          </div>
                        </div>

                        <div className="task-form-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
                          <div className="task-form-group">
                            <label className="task-form-label">Est. Hours</label>
                            <input
                              type="number"
                              step="0.1"
                              min="0"
                              className="task-form-input"
                              placeholder="e.g. 1.5"
                              value={newTaskData.estimated_hours || ''}
                              onChange={(e) => {
                                const val = e.target.value;
                                setNewTaskData(prev => ({
                                  ...prev,
                                  estimated_hours: val,
                                  estimated_minutes: val !== '' ? Math.round(parseFloat(val) * 60) : ''
                                }));
                              }}
                            />
                          </div>
                          <div className="task-form-group">
                            <label className="task-form-label">Est. Minutes</label>
                            <input
                              type="number"
                              min="0"
                              className="task-form-input"
                              placeholder="e.g. 90"
                              value={newTaskData.estimated_minutes || ''}
                              onChange={(e) => {
                                const val = e.target.value;
                                setNewTaskData(prev => ({
                                  ...prev,
                                  estimated_minutes: val,
                                  estimated_hours: val !== '' ? (parseInt(val, 10) / 60).toFixed(2) : ''
                                }));
                              }}
                            />
                          </div>
                          <div className="task-form-group">
                            <label className="task-form-label">Reminder Preference</label>
                            <select
                              className="task-form-select"
                              value={newTaskData.reminder_preference || 'none'}
                              onChange={(e) => setNewTaskData({...newTaskData, reminder_preference: e.target.value})}
                            >
                              <option value="none">No Reminder</option>
                              <option value="15m">15 minutes before</option>
                              <option value="30m">30 minutes before</option>
                              <option value="1h">1 hour before</option>
                              <option value="2h">2 hours before</option>
                              <option value="3h">3 hours before</option>
                              <option value="1d">1 day before</option>
                              <option value="custom">Custom Duration</option>
                            </select>"""

# Using regex to replace taking whitespace into account
target_regex = r'<div className="task-form-grid" style=\{\{ gridTemplateColumns: \'repeat\(3, 1fr\)\' \}\}>\s*<div className="task-form-group">\s*<label className="task-form-label">Start Date</label>[\s\S]*?<option value="custom">Custom Duration</option>\s*</select>'

replacement = """                        <div className="task-form-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
                          <div className="task-form-group">
                            <label className="task-form-label">Est. Hours</label>
                            <input
                              type="number"
                              step="0.1"
                              min="0"
                              className="task-form-input"
                              placeholder="e.g. 1.5"
                              value={newTaskData.estimated_hours || ''}
                              onChange={(e) => {
                                const val = e.target.value;
                                setNewTaskData(prev => ({
                                  ...prev,
                                  estimated_hours: val,
                                  estimated_minutes: val !== '' ? Math.round(parseFloat(val) * 60) : ''
                                }));
                              }}
                            />
                          </div>
                          <div className="task-form-group">
                            <label className="task-form-label">Est. Minutes</label>
                            <input
                              type="number"
                              min="0"
                              className="task-form-input"
                              placeholder="e.g. 90"
                              value={newTaskData.estimated_minutes || ''}
                              onChange={(e) => {
                                const val = e.target.value;
                                setNewTaskData(prev => ({
                                  ...prev,
                                  estimated_minutes: val,
                                  estimated_hours: val !== '' ? (parseInt(val, 10) / 60).toFixed(2) : ''
                                }));
                              }}
                            />
                          </div>
                          <div className="task-form-group">
                            <label className="task-form-label">Manual Due Date (Optional)</label>
                            <input
                              type="date"
                              className="task-form-input"
                              value={newTaskData.due_date || ''}
                              onChange={(e) => setNewTaskData({...newTaskData, due_date: e.target.value})}
                            />
                          </div>
                        </div>

                        <div className="task-form-grid" style={{ gridTemplateColumns: 'repeat(2, 1fr)' }}>
                          <div className="task-form-group">
                            <label className="task-form-label">Reminder Preference</label>
                            <select
                              className="task-form-select"
                              value={newTaskData.reminder_preference || 'none'}
                              onChange={(e) => setNewTaskData({...newTaskData, reminder_preference: e.target.value})}
                            >
                              <option value="none">No Reminder</option>
                              <option value="15m">15 minutes before</option>
                              <option value="30m">30 minutes before</option>
                              <option value="1h">1 hour before</option>
                              <option value="2h">2 hours before</option>
                              <option value="3h">3 hours before</option>
                              <option value="1d">1 day before</option>
                              <option value="custom">Custom Duration</option>
                            </select>"""

content = re.sub(target_regex, replacement, content)

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("App.jsx UI simplified")
