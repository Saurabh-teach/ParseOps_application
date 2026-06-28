with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Searching for getGoalDetail:")
for i, line in enumerate(lines):
    if 'getGoalDetail' in line:
        print(f"L{i+1}: {line.strip()[:100]}")

print("\nSearching for updateOrgTask:")
for i, line in enumerate(lines):
    if 'updateOrgTask' in line:
        print(f"L{i+1}: {line.strip()[:100]}")
