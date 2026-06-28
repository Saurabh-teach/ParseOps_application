with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'Linked Goal' in line:
        print(f"Occurrence found at line {i+1}: {line.strip()}")
        # Print next 20 lines
        for j in range(i+1, min(len(lines), i+25)):
             print(f"  Line {j+1}: {lines[j].strip()}")
        print("-" * 50)
