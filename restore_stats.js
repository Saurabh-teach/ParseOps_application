const fs = require('fs');
const { execSync } = require('child_process');

try {
    let pristine = execSync('git show HEAD:frontend/src/App.jsx', { encoding: 'utf8' });
    
    // Find getMemberStats in pristine
    const funcMatch = pristine.match(/(const getMemberStats = [\s\S]*?\n  \};)/);
    
    if (funcMatch) {
        let current = fs.readFileSync('frontend/src/App.jsx', 'utf8');
        
        // Ensure it's not already there
        if (!current.includes('const getMemberStats =')) {
            // Find a good place to put it. For example, right before 'const handleLoadComments'
            const anchor = 'const handleLoadComments =';
            const anchorIdx = current.indexOf(anchor);
            if (anchorIdx !== -1) {
                current = current.slice(0, anchorIdx) + funcMatch[1] + '\n\n  ' + current.slice(anchorIdx);
                fs.writeFileSync('frontend/src/App.jsx', current, 'utf8');
                console.log("SUCCESS: getMemberStats has been restored!");
            } else {
                console.log("Anchor handleLoadComments not found.");
            }
        } else {
            console.log("getMemberStats is already in the file!");
        }
    } else {
        console.log("Could not find getMemberStats in git history.");
    }
} catch (e) {
    console.error(e);
}
