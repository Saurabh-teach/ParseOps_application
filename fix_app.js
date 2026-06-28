const fs = require('fs');
const path = require('path');

const appPath = path.join(__dirname, 'frontend', 'src', 'App.jsx');

console.log("Reading App.jsx...");
let content = fs.readFileSync(appPath, 'utf8');

// Normalize line endings to LF for easier manipulation
content = content.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

// 1. Extract schedulePreview block
const schedRegex = /(  const \[schedulePreview[\s\S]*?schedulePreview\.manualOverride\]\);\n)/;
const matchSched = content.match(schedRegex);

if (matchSched) {
    const schedBlock = matchSched[1];
    content = content.replace(schedBlock, "");
    
    // 2. Find newTaskData block
    const newTaskRegex = /(  const \[newTaskData, setNewTaskData\] = useState\(\{[\s\S]*?risk: 'medium'\n  \}\);)/;
    const matchNewTask = content.match(newTaskRegex);
    
    if (matchNewTask) {
        const newTaskBlock = matchNewTask[1];
        
        // 3. Insert schedulePreview AFTER newTaskData
        content = content.replace(newTaskBlock, newTaskBlock + "\n\n" + schedBlock);
        
        fs.writeFileSync(appPath, content, 'utf8');
        console.log("Successfully fixed the hook order in App.jsx! Vite should hot-reload and the crash will disappear.");
    } else {
        console.log("Error: Could not find the newTaskData block. It may have been modified.");
    }
} else {
    console.log("Error: Could not find the schedulePreview block. The patch may not have applied correctly.");
}
