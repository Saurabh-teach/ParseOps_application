with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Normalize line endings
content = content.replace('\r\n', '\n').replace('\r', '\n')

# Replace the first error block (Goal details click handler)
old_goal_click = """                              onClick={async () => {
                                setLoading(true);
                                try {
                                  const detail = await getGoalDetail(goal.id);
                                  setLoading(false);
                                }
                                }}"""

new_goal_click = """                              onClick={async () => {
                                setLoading(true);
                                try {
                                  const detail = await getGoalDetail(goal.id);
                                  setActiveGoal(detail);
                                  setGoalsView('detail');
                                } catch (e) {
                                  console.error(e);
                                } finally {
                                  setLoading(false);
                                }
                              }}"""

# Replace the second error block (onChange task goal update)
old_task_goal = """                          onChange={async (e) => {
                            try {
                              const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { goal: e.target.value || null });
                              setActiveTask(updated);
                              handleLoadTasks();
                            } catch (err) {
                            ))}
                      </select>"""

new_task_goal = """                          onChange={async (e) => {
                            try {
                              const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { goal: e.target.value || null });
                              setActiveTask(updated);
                              handleLoadTasks();
                            } catch (err) {
                              console.error(err);
                            }
                          }}
                        >"""

# Perform replacements
print("Replacing goal click handler...")
if old_goal_click.replace('\r\n', '\n') in content:
    content = content.replace(old_goal_click.replace('\r\n', '\n'), new_goal_click)
    print("  -> Success!")
else:
    print("  -> Goal click handler target not found")

print("Replacing task goal update...")
if old_task_goal.replace('\r\n', '\n') in content:
    content = content.replace(old_task_goal.replace('\r\n', '\n'), new_task_goal)
    print("  -> Success!")
else:
    print("  -> Task goal update target not found")

# Save file back
with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Saved App.jsx")
