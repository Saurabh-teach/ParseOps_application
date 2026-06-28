import sys
import re
import os

file_path = r"c:\Users\saura\ParseOps\frontend\src\App.jsx"

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
except UnicodeDecodeError:
    with open(file_path, 'r', encoding='utf-16le') as f:
        content = f.read()

original_content = content

# 1. Remove the duplicated block
push_notif = "if (event.data && event.data.type === 'PUSH_NOTIFICATION') {"
end_marker = "const [tasksLayout, setTasksLayout] = useState('list'); // 'list' or 'board'"

parts = content.split(push_notif)
if len(parts) >= 3:
    end_idx = parts[2].find(end_marker)
    if end_idx != -1:
        remainder = parts[2][end_idx + len(end_marker):]
        # Remove any immediate trailing newlines
        while remainder.startswith('\n') or remainder.startswith('\r'):
            remainder = remainder[1:]
            
        content = parts[0] + push_notif + parts[1] + remainder
        print("Fixed duplicated PUSH_NOTIFICATION block.")

# 2. Fix the misplaced if statements and the premature closing of App()
# The premature closing of App() is `);\n  }\n` right before `if (view === 'connecting_sso') {`
# The `if` statements continue until the end of the file.
# They are: `if (view === 'connecting_sso')`, `if (view === 'initializing')`, `if (view === 'force_password_change')`
# We need to extract them and move them to right BEFORE the main `return (` of the App component.

# First, find the early returns block.
early_returns_start = content.find("if (view === 'connecting_sso') {")

if early_returns_start != -1:
    # Look backwards from early_returns_start to find the `);` and `}` that prematurely closed App().
    pre_text = content[:early_returns_start]
    
    # We want to remove the last `);` and `}`.
    match = re.search(r'\);\s*}\s*$', pre_text)
    if match:
        content = content[:match.start()] + content[early_returns_start:]
        print("Removed premature closing of App().")
    
    # Now `content` has the `if` blocks inside the main return (or at the bottom).
    # Wait, if we remove `); }`, then the main `return (` will just continue, which is INVALID JSX.
    # So we need to MOVE the `if` blocks.
    
    # Where does the `if` block end?
    # It ends right before `export default App;`
    export_idx = content.find("export default App;")
    if export_idx != -1:
        # Extract the entire `if` blocks chunk.
        # It starts at `early_returns_start` (which shifted if we removed `); }`, so let's find it again)
        new_early_returns_start = content.find("if (view === 'connecting_sso') {")
        
        # However, at the bottom of the file we should have `);\n}\nexport default App;`
        # Because we removed it from the middle!
        # The `if` blocks currently contain their own returns, but they end with `}`.
        # Let's extract the `if` blocks.
        
        # The `if` blocks end where `export default App;` begins.
        # Wait, there's another `);` and `}` at the very end of the file?
        # Let's check the very end of the original file.
        # It had:
        #   );
        # }
        # export default App;
        # NO! The original file had `if (view === 'force_password_change') { ... }` 
        # Then maybe a random `);` and `}`?
        # Let's find the exact text from `if (view === 'connecting_sso')` to `export default App;`
        
        chunk = content[new_early_returns_start:export_idx]
        
        # We need to remove this chunk from the bottom.
        content = content[:new_early_returns_start] + "\n  );\n}\n\n" + content[export_idx:]
        
        # Now we need to INSERT the chunk right BEFORE the main `return (` of App().
        # The main return usually looks like `return (` followed by some JSX.
        # It should be the LAST `return (` BEFORE `new_early_returns_start`.
        # Actually, let's find `return (` that starts the main JSX.
        # `return (` with `<div className="app-container">` is a good bet.
        main_return_match = re.search(r'return\s*\(\s*<div[^>]*className=["\']app-container["\']', content)
        if main_return_match:
            insert_pos = main_return_match.start()
            content = content[:insert_pos] + chunk + "\n  " + content[insert_pos:]
            print("Moved early return blocks to before the main return.")
        else:
            print("Could not find main return block!")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done fixing App.jsx!")
