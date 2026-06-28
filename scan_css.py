with open('c:/Users/saura/ParseOps/frontend/src/index.css', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'slim' in line or 'nav' in line:
        print(f"Line {i+1}: {line.strip()[:100]}")
