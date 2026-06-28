with open('c:/Users/saura/ParseOps/frontend/src/App_recovered_actual.jsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
hash_lines = []
for i, line in enumerate(lines):
    if line.strip().startswith('#'):
         hash_lines.append((i+1, line.strip()))

print(f"Found {len(hash_lines)} hash lines:")
for num, text in hash_lines[:100]:
    print(f"  Line {num}: {text}")
