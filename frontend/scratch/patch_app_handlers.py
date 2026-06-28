import re

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

target = """                  <WorkspaceCalendar 
                    selectedOrg={selectedOrg} 
                    handleTaskClick={handleViewTaskDetails} 
                    handleGoalClick={setActiveGoalId} 
                  />"""

replacement = """                  <WorkspaceCalendar 
                    selectedOrg={selectedOrg} 
                    handleTaskClick={(id) => { setActiveTab('tasks'); handleTaskClick({ id }); }} 
                    handleGoalClick={async (id) => { 
                      try { 
                        const detail = await getGoalDetail(id); 
                        setActiveGoal(detail); 
                        setGoalsView('detail'); 
                        setActiveTab('goals'); 
                      } catch(e){ console.error(e); } 
                    }} 
                  />"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("App.jsx patched for correct event handlers")
