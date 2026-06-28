const fs = require('fs');
const lines = fs.readFileSync('frontend/src/App.jsx', 'utf8').split(/\r?\n/);

console.log("--- START DEBUG ---");
for (let i = 1960; i < 1990; i++) {
    if (lines[i] !== undefined) {
        console.log(i + ': ' + lines[i]);
    }
}
console.log("--- END DEBUG ---");
