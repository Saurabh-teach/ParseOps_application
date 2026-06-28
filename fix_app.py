import sys
import re

app_jsx_path = r'c:\Users\saura\ParseOps\frontend\src\App.jsx'

with open(app_jsx_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to capture the entire schedulePreview block (useState + useEffect)
pattern_schedule = r"(  const \[schedulePreview.*?\[newTaskData\.assignees.*?schedulePreview\.manualOverride\]\);\s*)"

match_schedule = re.search(pattern_schedule, content, re.DOTALL)
if match_schedule:
    extracted_block = match_schedule.group(1)
    
    # Remove it from content
    content = content.replace(extracted_block, "")
    
    # Now find newTaskData state initialization and insert AFTER it
    pattern_new_task = r"(  const \[newTaskData, setNewTaskData\] = useState\(\{[\s\S]*?risk: 'medium'[\s\S]*?\}\);)"
    match_new_task = re.search(pattern_new_task, content)
    
    if match_new_task:
        new_task_block = match_new_task.group(1)
        # Replace the new_task_block with itself + extracted_block
        content = content.replace(new_task_block, new_task_block + "\n\n" + extracted_block)
        
        with open(app_jsx_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Successfully fixed the initialization order in App.jsx! The app should now work without crashing.")
    else:
        print("Failed to find newTaskData block. Please check the file contents.")
else:
    print("Failed to find schedulePreview block. Please check the file contents.")
