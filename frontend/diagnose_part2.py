import re

file_path = r"c:\Users\saura\ParseOps\frontend\src\App.jsx"
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines before clean: {len(lines)}")

# Find the main return block
main_return = -1
for idx, line in enumerate(lines):
    if 'className="app-container"' in line or "className='app-container'" in line:
        # Check if previous lines contain return (
        for i in range(idx, max(-1, idx-10), -1):
            if 'return' in lines[i]:
                main_return = i
                break
        if main_return != -1:
            break

print(f"Main return starts at line: {main_return + 1}")

# Check duplicate doDrag, stopDrag, isAssignee, goalObj, matchesSearch, isNewMember
funcs = ['doDrag', 'stopDrag', 'isAssignee', 'goalObj', 'matchesSearch', 'isNewMember']
for func in funcs:
    print(f"\nOccurrences of {func}:")
    for idx, line in enumerate(lines):
        if re.search(rf'(?:const|function|let)\s+{func}\s*=?\s*\(', line):
            print(f"  Line {idx+1}: {line.strip()}")
