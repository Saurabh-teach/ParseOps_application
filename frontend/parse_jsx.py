file_path = r"c:\Users\saura\ParseOps\frontend\src\App.jsx"

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
except UnicodeDecodeError:
    with open(file_path, 'r', encoding='utf-16le') as f:
        lines = f.readlines()

print(f"Total lines: {len(lines)}")

sso_line = -1
for idx, line in enumerate(lines):
    if "view === 'connecting_sso'" in line:
        sso_line = idx
        break

if sso_line != -1:
    print(f"\n--- Context around line {sso_line + 1} ---")
    start = max(0, sso_line - 15)
    end = min(len(lines), sso_line + 25)
    for i in range(start, end):
        print(f"{i + 1}: {lines[i]}", end='')
else:
    print("Could not find connecting_sso line!")
