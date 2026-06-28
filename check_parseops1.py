import os

path1 = r"c:\Users\saura\ParseOps1\frontend\src"
if os.path.exists(path1):
    print("Files in ParseOps1/frontend/src:")
    for f in os.listdir(path1):
        fp = os.path.join(path1, f)
        print(f"  {f}: {os.path.getsize(fp)} bytes")
else:
    print("ParseOps1/frontend/src does not exist")
