with open('c:/Users/saura/ParseOps/frontend/src/App_recovered_actual.jsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

# Search for starts
for i, line in enumerate(lines):
    if 'import ' in line and i < 50:
         print(f"Line {i+1}: {line.strip()[:100]}")
    if 'function App' in line:
         print(f"Line {i+1}: {line.strip()[:100]}")
    if 'export default' in line:
         print(f"Line {i+1}: {line.strip()[:100]}")
