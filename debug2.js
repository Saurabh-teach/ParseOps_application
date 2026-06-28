const fs = require('fs');
const lines = fs.readFileSync('frontend/src/App.jsx', 'utf8').split(/\r?\n/);

for (let i = 0; i < lines.length; i++) {
    if (lines[i].includes('isFreeMembersModalOpen')) {
        console.log("FOUND AT LINE " + (i + 1));
        for(let j = i - 5; j <= i + 5; j++) {
            console.log(j + 1 + ': ' + lines[j]);
        }
    }
}
