import os

app_path = r'c:\Users\saura\ParseOps\frontend\src\App.jsx'
with open(app_path, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'Loading' in line or 'loading' in line:
        print(f"Line {i+1}: {line.strip()}")
