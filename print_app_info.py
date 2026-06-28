import os

path = 'c:/Users/saura/ParseOps/frontend/src/App.jsx'
if os.path.exists(path):
    print(f"File size: {os.path.getsize(path)} bytes")
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    print(f"Total lines: {len(lines)}")
    print("First 10 lines:")
    for l in lines[:10]:
        print(f"  {repr(l)}")
    print("Last 10 lines:")
    for l in lines[-10:]:
        print(f"  {repr(l)}")
else:
    print("File does not exist!")
