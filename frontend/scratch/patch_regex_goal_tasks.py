import re

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace start_date and due_date in initial state
content = re.sub(
    r"title:\s*'',\s*start_date:\s*'',\s*due_date:\s*'',\s*assignees:\s*\[\]",
    r"title: '', estimated_hours: '', estimated_minutes: '', assignees: []",
    content
)

# Replace the payload part
payload_regex = r"start_date:\s*goalTaskForm\.start_date\s*\|\|\s*undefined,\s*due_date:\s*goalTaskForm\.due_date\s*\|\|\s*undefined,"
payload_replacement = "estimated_hours: goalTaskForm.estimated_hours || 0,\n\n        estimated_minutes: goalTaskForm.estimated_minutes || 0,"
content = re.sub(payload_regex, payload_replacement, content)

# Remove the old deletes
content = re.sub(
    r"if\s*\(!payload\.start_date\)\s*delete\s*payload\.start_date;\s*if\s*\(!payload\.due_date\)\s*delete\s*payload\.due_date;",
    "",
    content
)

# Replace UI portion
ui_regex = r"<label className=\"input-label\" style=\{\{\s*fontSize:\s*'0.7rem'\s*\}\}>Start Date</label>[\s\S]*?<input[\s\S]*?type=\"date\"[\s\S]*?className=\"input-field\"[\s\S]*?value=\{goalTaskForm\.start_date\}[\s\S]*?onChange=\{\(e\)\s*=>\s*setGoalTaskForm\(\{\.\.\.goalTaskForm,\s*start_date:\s*e\.target\.value\}\)\}[\s\S]*?style=\{\{\s*padding:\s*'0.45rem',\s*fontSize:\s*'0.8rem'\s*\}\}[\s\S]*?/>[\s\S]*?</div>[\s\S]*?<div className=\"input-group\">[\s\S]*?<label className=\"input-label\" style=\{\{\s*fontSize:\s*'0.7rem'\s*\}\}>Due Date</label>[\s\S]*?<input[\s\S]*?type=\"date\"[\s\S]*?className=\"input-field\"[\s\S]*?value=\{goalTaskForm\.due_date\}[\s\S]*?onChange=\{\(e\)\s*=>\s*setGoalTaskForm\(\{\.\.\.goalTaskForm,\s*due_date:\s*e\.target\.value\}\)\}[\s\S]*?style=\{\{\s*padding:\s*'0.45rem',\s*fontSize:\s*'0.8rem'\s*\}\}[\s\S]*?/>"

ui_replacement = """<label className="input-label" style={{ fontSize: '0.7rem' }}>Est. Hours</label>
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
                                      />"""
content = re.sub(ui_regex, ui_replacement, content)

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("App.jsx heavily patched via regex")
