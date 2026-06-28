with open('c:/Users/saura/ParseOps/frontend/src/App_recovered_actual.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

# Find all occurrences of "return (" in the file
import re
matches = [m.start() for m in re.finditer(r'return\s*\(', text)]
print(f"Total 'return (' matches: {len(matches)}")
for idx, pos in enumerate(matches):
    # Print the line number and surrounding text
    line_num = text[:pos].count('\n') + 1
    print(f"Occurrence {idx+1} at line {line_num} (char {pos}):")
    print(text[pos:pos+150].strip().replace('\n', ' '))
    print()
