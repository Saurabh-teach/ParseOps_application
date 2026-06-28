const fs = require('fs');
const content = fs.readFileSync('frontend/src/App.jsx', 'utf8');
const lines = content.split(/\r?\n/);

let out = [];
for (let i = 0; i < lines.length; i++) {
    if (lines[i].includes('schedulePreview') || lines[i].includes('newTaskData')) {
        out.push(`${i}: ${lines[i]}`);
    }
}

fs.writeFileSync('C:/Users/saura/.gemini/antigravity-ide/brain/b8db8461-6f3d-4d60-84fb-ee41aef32f15/scratch/out.txt', out.join('\n'));
