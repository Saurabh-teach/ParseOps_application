with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Show the blocks before fixing
print("BEFORE GOAL DETAIL FIX:")
for idx in range(3930, 3942):
    print(f"L{idx+1}: {lines[idx].rstrip()}")

print("\nBEFORE TASK GOAL FIX:")
for idx in range(5148, 5162):
    print(f"L{idx+1}: {lines[idx].rstrip()}")

# Let's perform replacements by line numbers (0-indexed)
# L3933 to L3939 corresponds to indices 3932 to 3938
lines[3932:3939] = [
    "                              onClick={async () => {\n",
    "                                setLoading(true);\n",
    "                                try {\n",
    "                                  const detail = await getGoalDetail(goal.id);\n",
    "                                  setActiveGoal(detail);\n",
    "                                  setGoalsView('detail');\n",
    "                                } catch (e) {\n",
    "                                  console.error(e);\n",
    "                                } finally {\n",
    "                                  setLoading(false);\n",
    "                                }\n",
    "                              }}\n"
]

# Let's search again for 'updateOrgTask' with goal value to find its new index
# because inserting lines above might have shifted the lines below.
for idx, line in enumerate(lines):
    if 'updateOrgTask' in line and 'goal: e.target.value' in line and idx > 4000 and idx < 6000:
         task_goal_idx = idx
         break

print(f"\nNew task goal select index: {task_goal_idx}")
# We want to replace from the start of try (task_goal_idx - 1) to the corrupted close (task_goal_idx + 4)
# Let's see what is there
for idx in range(task_goal_idx - 2, task_goal_idx + 6):
    print(f"L{idx+1}: {lines[idx].rstrip()}")

lines[task_goal_idx - 1 : task_goal_idx + 5] = [
    "                            try {\n",
    "                              const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { goal: e.target.value || null });\n",
    "                              setActiveTask(updated);\n",
    "                              handleLoadTasks();\n",
    "                            } catch (err) {\n",
    "                              console.error(err);\n",
    "                            }\n",
    "                          }}\n",
    "                        >\n"
]

# Save file back
with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("\nSuccessfully updated App.jsx!")
