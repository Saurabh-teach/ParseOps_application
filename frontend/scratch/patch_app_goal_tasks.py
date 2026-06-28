import re

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update initial states
content = content.replace("const [goalTaskForm, setGoalTaskForm] = useState({\n    title: '',\n    start_date: '',\n    due_date: '',\n    assignees: []\n  });", "const [goalTaskForm, setGoalTaskForm] = useState({\n    title: '',\n    estimated_hours: '',\n    estimated_minutes: '',\n    assignees: []\n  });")

content = content.replace("setGoalTaskForm({ title: '', start_date: '', due_date: '', assignees: [] });", "setGoalTaskForm({ title: '', estimated_hours: '', estimated_minutes: '', assignees: [] });")

# 2. Update handleCreateGoalTask
target_handle = """      const payload = {
        title: goalTaskForm.title,
        start_date: goalTaskForm.start_date || undefined,
        due_date: goalTaskForm.due_date || undefined,
        assignees: goalTaskForm.assignees,
        goal: activeGoal.id,
        organization: selectedOrg.id,
        issue_type: 'task',
        priority: 'medium',
        status: 'todo',
        visibility_type: 'specific',
      };
      
      if (!payload.start_date) delete payload.start_date;
      if (!payload.due_date) delete payload.due_date;"""

replacement_handle = """      const payload = {
        title: goalTaskForm.title,
        estimated_hours: goalTaskForm.estimated_hours || 0,
        estimated_minutes: goalTaskForm.estimated_minutes || 0,
        assignees: goalTaskForm.assignees,
        goal: activeGoal.id,
        organization: selectedOrg.id,
        issue_type: 'task',
        priority: 'medium',
        status: 'todo',
        visibility_type: 'specific',
      };"""

content = content.replace(target_handle, replacement_handle)

# 3. Update the UI Form
target_ui = """                                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                                    <div className="input-group">
                                      <label className="input-label" style={{ fontSize: '0.7rem' }}>Start Date</label>
                                      <input 
                                        type="date"
                                        className="input-field"
                                        value={goalTaskForm.start_date}
                                        onChange={(e) => setGoalTaskForm({...goalTaskForm, start_date: e.target.value})}
                                        style={{ padding: '0.45rem', fontSize: '0.8rem' }}
                                      />
                                    </div>
                                    <div className="input-group">
                                      <label className="input-label" style={{ fontSize: '0.7rem' }}>Due Date</label>
                                      <input 
                                        type="date"
                                        className="input-field"
                                        value={goalTaskForm.due_date}
                                        onChange={(e) => setGoalTaskForm({...goalTaskForm, due_date: e.target.value})}
                                        style={{ padding: '0.45rem', fontSize: '0.8rem' }}
                                      />
                                    </div>
                                  </div>"""

replacement_ui = """                                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                                    <div className="input-group">
                                      <label className="input-label" style={{ fontSize: '0.7rem' }}>Est. Hours</label>
                                      <input 
                                        type="number"
                                        min="0"
                                        placeholder="e.g. 2"
                                        className="input-field"
                                        value={goalTaskForm.estimated_hours}
                                        onChange={(e) => setGoalTaskForm({...goalTaskForm, estimated_hours: e.target.value})}
                                        style={{ padding: '0.45rem', fontSize: '0.8rem' }}
                                      />
                                    </div>
                                    <div className="input-group">
                                      <label className="input-label" style={{ fontSize: '0.7rem' }}>Est. Minutes</label>
                                      <input 
                                        type="number"
                                        min="0"
                                        max="59"
                                        placeholder="e.g. 30"
                                        className="input-field"
                                        value={goalTaskForm.estimated_minutes}
                                        onChange={(e) => setGoalTaskForm({...goalTaskForm, estimated_minutes: e.target.value})}
                                        style={{ padding: '0.45rem', fontSize: '0.8rem' }}
                                      />
                                    </div>
                                  </div>"""

content = content.replace(target_ui, replacement_ui)

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("App.jsx patched for Goal Linked Tasks Form")
