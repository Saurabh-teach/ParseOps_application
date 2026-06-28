"""Diagnose all issues in App.jsx"""
import re

file_path = r"c:\Users\saura\ParseOps\frontend\src\App.jsx"
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

# 1. Find duplicate useState declarations
state_decls = {}
for idx, line in enumerate(lines):
    m = re.search(r'const \[(\w+), set\w+\] = useState', line)
    if m:
        name = m.group(1)
        if name not in state_decls:
            state_decls[name] = []
        state_decls[name].append(idx + 1)

print("\n=== DUPLICATE useState DECLARATIONS ===")
for name, locs in state_decls.items():
    if len(locs) > 1:
        print(f"  {name}: lines {locs}")

# 2. Find duplicate function declarations
func_decls = {}
for idx, line in enumerate(lines):
    m = re.search(r'(?:const|function)\s+(\w+)\s*=?\s*(?:async\s*)?\(', line)
    if m:
        name = m.group(1)
        if name not in func_decls:
            func_decls[name] = []
        func_decls[name].append(idx + 1)

print("\n=== DUPLICATE FUNCTION DECLARATIONS ===")
for name, locs in func_decls.items():
    if len(locs) > 1:
        print(f"  {name}: lines {locs}")

# 3. Find dangling code (code outside function/component bodies)
# Look for lines with 'if (event.data' outside useEffect
print("\n=== DANGLING EVENT HANDLERS ===")
for idx, line in enumerate(lines):
    stripped = line.strip()
    if "if (event.data && event.data.type === 'PUSH_NOTIFICATION')" in stripped:
        print(f"  Line {idx+1}: {stripped[:80]}")

# 4. Check for 'connecting_sso', 'initializing', 'force_password_change' early returns
print("\n=== EARLY RETURN VIEWS ===")
for keyword in ['connecting_sso', 'initializing', 'force_password_change']:
    found = [(idx+1, lines[idx].strip()[:80]) for idx, line in enumerate(lines) if keyword in line]
    print(f"  '{keyword}' found at: {[f[0] for f in found] if found else 'MISSING!'}")

# 5. Find 'function App()' declaration
print("\n=== App() DECLARATION ===")
for idx, line in enumerate(lines):
    if 'function App()' in line:
        print(f"  Line {idx+1}: {line.strip()}")

# 6. Find 'export default App'
print("\n=== EXPORT DEFAULT ===")
for idx, line in enumerate(lines):
    if 'export default App' in line:
        print(f"  Line {idx+1}: {line.strip()}")

# 7. Check for profileData references
print("\n=== profileData REFERENCES ===")
profile_lines = [idx+1 for idx, line in enumerate(lines) if 'profileData' in line]
print(f"  Referenced at {len(profile_lines)} lines. First 5: {profile_lines[:5]}")
# Check if it's defined
profile_defs = [idx+1 for idx, line in enumerate(lines) if re.search(r'const \[profileData', line)]
print(f"  Defined at: {profile_defs if profile_defs else 'NOT DEFINED!'}")

# 8. Check undefined variables
for varname in ['newTaskData', 'selectedOrg', 'profileData', 'historySubTab', 'handleLoadTasks']:
    defs = []
    for idx, line in enumerate(lines):
        if re.search(rf'(?:const|let|var|function)\s+(?:\[?{varname})', line):
            defs.append(idx+1)
    refs = sum(1 for line in lines if varname in line)
    print(f"\n  {varname}: defined at {defs if defs else 'NOT DEFINED!'}, referenced {refs} times")

# 9. Find the duplicate block region
# The user's paste showed a duplicate block starting with PUSH_NOTIFICATION handler
# followed by duplicate state declarations. Let's find the exact region.
print("\n=== LOOKING FOR DUPLICATE BLOCK BOUNDARIES ===")
# Find all occurrences of specific unique-ish state
for marker in ["const [activeTabState, setActiveTabState]", "const [sharingModalConfig, setSharingModalConfig]"]:
    found = [idx+1 for idx, line in enumerate(lines) if marker in line]
    print(f"  '{marker[:50]}...' at lines: {found}")
