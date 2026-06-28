const fs = require('fs');
const path = 'c:/Users/saura/ParseOps/frontend/src/App.jsx';

let content = fs.readFileSync(path, 'utf8');

// Normalize all line endings to \r\n (Windows CRLF)
content = content.replace(/\r\n/g, '\n').replace(/\r/g, '\n').replace(/\n/g, '\r\n');

fs.writeFileSync(path, content, 'utf8');

const lineCount = content.split('\r\n').length;
const opens = (content.match(/\{/g) || []).length;
const closes = (content.match(/\}/g) || []).length;

console.log(`Done. Normalized ${lineCount} lines.`);
console.log(`Braces: { = ${opens}, } = ${closes}, diff = ${opens - closes}`);
