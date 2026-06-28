with open('c:/Users/saura/ParseOps/frontend/src/App_recovered_actual.jsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines in file: {len(lines)}")
backtick_lines = []
for i, line in enumerate(lines):
    if line.strip().startswith('```'):
        backtick_lines.append((i+1, line.strip()))

print(f"Found {len(backtick_lines)} lines with backticks:")
for num, text in backtick_lines[:50]:
    print(f"  Line {num}: {text}")
