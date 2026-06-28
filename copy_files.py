import os
import shutil

# Copy ParseOps1 App.jsx
src1 = r"c:\Users\saura\ParseOps1\frontend\src\App.jsx"
dst1 = r"c:\Users\saura\ParseOps\frontend\src\App_ParseOps1.jsx"

if os.path.exists(src1):
    shutil.copy2(src1, dst1)
    print(f"Copied {src1} to {dst1} ({os.path.getsize(dst1)} bytes)")
else:
    print(f"Source {src1} does not exist")

# Copy ParseOps2 App.tsx or App.jsx if it exists
src2_jsx = r"c:\Users\saura\ParseOps2\frontend\src\App.jsx"
src2_tsx = r"c:\Users\saura\ParseOps2\frontend\src\App.tsx"
dst2 = r"c:\Users\saura\ParseOps\frontend\src\App_ParseOps2_actual.jsx"

if os.path.exists(src2_jsx):
    shutil.copy2(src2_jsx, dst2)
    print(f"Copied {src2_jsx} to {dst2} ({os.path.getsize(dst2)} bytes)")
elif os.path.exists(src2_tsx):
    shutil.copy2(src2_tsx, dst2)
    print(f"Copied {src2_tsx} to {dst2} ({os.path.getsize(dst2)} bytes)")
else:
    print("No ParseOps2 App.jsx/App.tsx found")
