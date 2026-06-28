import os

print("Searching for large backup files in your project...")

root_dir = r"c:\Users\saura\ParseOps"

for root, dirs, files in os.walk(root_dir):
    if 'node_modules' in root or 'myenv' in root or '.vscode' in root or '.git' in root:
        continue
    for file in files:
        if file.endswith('.jsx') or file.endswith('.txt') or file.endswith('.bak') or file.endswith('.js') or 'backup' in file.lower() or 'old' in file.lower():
            file_path = os.path.join(root, file)
            try:
                size = os.path.getsize(file_path)
                if size > 100000: # larger than 100KB
                    print(f"FOUND LARGE FILE: {file_path} ({size} bytes)")
            except Exception:
                pass
print("Search complete.")
