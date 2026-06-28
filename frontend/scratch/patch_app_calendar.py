import re

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Import injection
import_target = """import { \n  loginRequest, """
import_replacement = """import WorkspaceCalendar from './components/CalendarView';\nimport { \n  loginRequest, """
content = content.replace(import_target, import_replacement)

# Calendar block replacement
block_regex = r"\{activeTab === 'calendar' && \(\(\) => \{[\s\S]*?No events scheduled this month</p>\s*<p style=\{\{ fontSize: '0.8rem', marginTop: '0.25rem' \}\}>Event scheduling coming soon</p>\s*</div>\s*</div>\s*\);\s*\}\)\(\)\}"

replacement = """{activeTab === 'calendar' && (
              <div style={{ maxWidth: '1200px', margin: '0 auto', height: '100%', display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                  <div>
                    <h2 className="section-title-premium" style={{ marginBottom: '0.25rem' }}>Workspace Calendar</h2>
                    <p style={{ fontSize: '0.9rem', color: '#64748b', margin: 0 }}>{selectedOrg?.name} • Drag & Drop to Reschedule</p>
                  </div>
                </div>
                <div style={{ flex: 1, minHeight: '600px' }}>
                  <WorkspaceCalendar 
                    selectedOrg={selectedOrg} 
                    handleTaskClick={handleViewTaskDetails} 
                    handleGoalClick={setActiveGoalId} 
                  />
                </div>
              </div>
            )}"""

content = re.sub(block_regex, replacement, content)

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("App.jsx patched for Calendar component")
