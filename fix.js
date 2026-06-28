const fs = require('fs');

const appPath = 'frontend/src/App.jsx';
let content = fs.readFileSync(appPath, 'utf8');

// First, find and extract the schedule preview block
const schedStartStr = '  const [schedulePreview, setSchedulePreview] = useState({';
const schedStart = content.indexOf(schedStartStr);

if (schedStart !== -1) {
    const endStr = 'schedulePreview.manualOverride]);';
    const endIdx = content.indexOf(endStr, schedStart);
    
    if (endIdx !== -1) {
        let blockEnd = endIdx + endStr.length;
        // consume trailing newlines
        while (content[blockEnd] === '\r' || content[blockEnd] === '\n') {
            blockEnd++;
        }
        
        const extractedBlock = content.slice(schedStart, blockEnd);
        content = content.slice(0, schedStart) + content.slice(blockEnd);
        
        // Now find newTaskData
        const ntdStartStr = '  const [newTaskData, setNewTaskData] = useState({';
        const ntdStart = content.indexOf(ntdStartStr);
        
        if (ntdStart !== -1) {
            // Find risk: 'medium' to know we are in the right block
            const riskIdx = content.indexOf("risk: 'medium'", ntdStart);
            if (riskIdx !== -1) {
                const closeIdx = content.indexOf('});', riskIdx);
                if (closeIdx !== -1) {
                    let insertPos = closeIdx + 3;
                    while (content[insertPos] === '\r' || content[insertPos] === '\n') {
                        insertPos++;
                    }
                    
                    // Re-insert extracted block perfectly
                    content = content.slice(0, insertPos) + '\n\n' + extractedBlock + '\n\n' + content.slice(insertPos);
                    fs.writeFileSync(appPath, content, 'utf8');
                    console.log("\n✅ SUCCESS! App.jsx has been fixed perfectly.");
                    console.log("Check your browser now, the crash should be gone!");
                } else {
                    console.log("Error: Could not find closing bracket for newTaskData");
                }
            } else {
                console.log("Error: Could not find risk: 'medium'");
            }
        } else {
            console.log("Error: Could not find newTaskData start");
        }
    } else {
        console.log("Error: Could not find end of schedule block");
    }
} else {
    console.log("Error: Could not find schedule block");
}
