with open('c:/Users/saura/ParseOps/frontend/src/App_recovered_actual.jsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Searching for 'slim-nav' starting from line 2697:")
for i in range(2696, len(lines)):
    line = lines[i]
    if 'slim-nav' in line:
        print(f"Line {i+1}: {line.strip()[:100]}")
