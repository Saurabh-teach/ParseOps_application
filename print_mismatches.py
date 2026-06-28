with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Goal details click handler block:")
for idx in range(3929, 3943):
    if idx < len(lines):
        print(f"L{idx+1}: {repr(lines[idx])}")

print("\nTask goal update block:")
for idx in range(5149, 5163):
    if idx < len(lines):
        print(f"L{idx+1}: {repr(lines[idx])}")
