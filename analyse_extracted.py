with open('c:/Users/saura/ParseOps/frontend/src/App_recovered_actual.jsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

# Find all lines starting with import React
import_indices = [i for i, line in enumerate(lines) if 'import React' in line]
print(f"Import React found at line indices: {import_indices}")

# Find all lines starting with export default function App
export_indices = [i for i, line in enumerate(lines) if 'export default function App' in line]
print(f"Export default function App found at line indices: {export_indices}")
