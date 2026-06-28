import re

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace the first error block (Goal details click handler)
# We match onClick={async () => { setLoading(true); try { const detail = await getGoalDetail(goal.id); setLoading(false); } }}
# taking any spacing into account.
pattern1 = r'onClick\s*=\s*\{\s*async\s*\(\s*\)\s*=>\s*\{\s*setLoading\s*\(\s*true\s*\)\s*;\s*try\s*\{\s*const\s+detail\s*=\s*await\s+getGoalDetail\s*\(\s*goal\.id\s*\)\s*;\s*setLoading\s*\(\s*false\s*\)\s*;\s*\}\s*\}\s*\}'

replacement1 = """onClick={async () => {
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

content, count1 = re.subn(pattern1, replacement1, content)
print(f"Goal click handler replaced {count1} times.")

# 2. Replace the second error block (onChange task goal update)
pattern2 = r'onChange\s*=\s*\{\s*async\s*\(\s*e\s*\)\s*=>\s*\{\s*try\s*\{\s*const\s+updated\s*=\s*await\s+updateOrgTask\s*\(\s*selectedOrg\.slug\s*,\s*activeTask\.id\s*,\s*\{\s*goal\s*:\s*e\.target\.value\s*\|\|\s*null\s*\}\s*\)\s*;\s*setActiveTask\s*\(\s*updated\s*\)\s*;\s*handleLoadTasks\s*\(\s*\)\s*;\s*\}\s*catch\s*\(\s*err\s*\)\s*\{\s*\}\s*\)\s*\}\s*\}\s*</select>'

# Wait, let's see. The catch block in content is:
# } catch (err) {
# ))
# }
# </select>
# Let's inspect what is exactly there in App.jsx:
# onChange={async (e) => {
#   try {
#     const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { goal: e.target.value || null });
#     setActiveTask(updated);
#     handleLoadTasks();
#   } catch (err) {
#   ))}
# </select>
pattern2_simple = r'onChange\s*=\s*\{\s*async\s*\(\s*e\s*\)\s*=>\s*\{\s*try\s*\{\s*const\s+updated\s*=\s*await\s+updateOrgTask\s*\(\s*selectedOrg\.slug\s*,\s*activeTask\.id\s*,\s*\{\s*goal\s*:\s*e\.target\.value\s*\|\|\s*null\s*\}\s*\)\s*;\s*setActiveTask\s*\(\s*updated\s*\)\s*;\s*handleLoadTasks\s*\(\s*\)\s*;\s*\}\s*catch\s*\(\s*err\s*\)\s*\{\s*\}\s*\)\s*\)\s*\}'

# Let's use a simpler regex that just targets line 5150 to 5160
# Let's search for "updateOrgTask(selectedOrg.slug, activeTask.id, { goal: e.target.value || null })" and replace everything from that try block to select.
pattern_task_goal = r'try\s*\{\s*const\s+updated\s*=\s*await\s+updateOrgTask\s*\(\s*selectedOrg\.slug\s*,\s*activeTask\.id\s*,\s*\{\s*goal\s*:\s*e\.target\.value\s*\|\|\s*null\s*\}\s*\)\s*;\s*setActiveTask\s*\(\s*updated\s*\)\s*;\s*handleLoadTasks\s*\(\s*\)\s*;\s*\}\s*catch\s*\(\s*err\s*\)\s*\{\s*\}\s*\)\s*\)\s*\}\s*</select>'

replacement_task_goal = """try {
                              const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { goal: e.target.value || null });
                              setActiveTask(updated);
                              handleLoadTasks();
                            } catch (err) {
                              console.error(err);
                            }
                          }}
                        >"""

# Let's try matching with a very loose regex
pattern_loose = r'try\s*\{\s*const\s+updated\s*=\s*await\s+updateOrgTask\s*\(\s*selectedOrg\.slug\s*,\s*activeTask\.id\s*,\s*\{\s*goal\s*:\s*e\.target\.value\s*\|\|\s*null\s*\}\s*\)\s*;\s*setActiveTask\s*\(\s*updated\s*\)\s*;\s*handleLoadTasks\s*\(\s*\)\s*;\s*\}\s*catch\s*\(err\)\s*\{\s*\}\s*\)\s*\)\s*\}'

replacement_loose = """try {
                              const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { goal: e.target.value || null });
                              setActiveTask(updated);
                              handleLoadTasks();
                            } catch (err) {
                              console.error(err);
                            }
                          }}"""

content, count2 = re.subn(pattern_loose, replacement_loose, content)
print(f"Task goal update replaced {count2} times.")

# Save file back
with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Saved App.jsx")
