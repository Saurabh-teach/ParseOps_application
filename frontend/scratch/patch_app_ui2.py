import re

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

target = r"\{planningData\.suggested_due_date && \(\s*<div style=\{\{ fontSize: '0.775rem', color: '#475569' \}\}>\s*Suggested due date \(6\.5h daily limit, no weekends\): <strong style=\{\{ color: '#4f46e5' \}\}>\{new Date\(planningData\.suggested_due_date\)\.toLocaleString\(\[\], \{ dateStyle: 'medium', timeStyle: 'short' \}\)\}<\/strong>\s*<\/div>\s*\)\}"

replacement = """{planningData.suggested_due_date && (
                                <div style={{ fontSize: '0.775rem', color: '#475569', display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                                  <span>Suggested due date (6.5h daily limit, no weekends): <strong style={{ color: '#4f46e5' }}>{new Date(planningData.suggested_due_date).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}</strong></span>
                                  <button 
                                    type="button" 
                                    onClick={() => setNewTaskData({...newTaskData, due_date: planningData.suggested_due_date.split('T')[0]})}
                                    style={{ padding: '0.15rem 0.4rem', fontSize: '0.7rem', background: '#eef2ff', color: '#4f46e5', border: '1px solid #c7d2fe', borderRadius: '4px', cursor: 'pointer' }}
                                  >
                                    Apply
                                  </button>
                                </div>
                              )}"""

content = re.sub(target, replacement, content)

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("App.jsx patched to add Apply button")
