import os
import json
import shutil
import urllib.parse

history_dir = r"c:\Users\saura\AppData\Roaming\Code\User\History"
output_file = r"c:\Users\saura\ParseOps\frontend\src\App_recovered.jsx"

print("Searching VS Code Local History using entries.json...")

best_file = None
best_time = 0

for folder in os.listdir(history_dir):
    folder_path = os.path.join(history_dir, folder)
    if not os.path.isdir(folder_path):
        continue
        
    entries_path = os.path.join(folder_path, 'entries.json')
    if not os.path.exists(entries_path):
        continue
        
    try:
        with open(entries_path, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
            
        resource = data.get('resource', '')
        # Check if this history folder belongs to App.jsx
        if 'App.jsx' in resource and 'frontend' in resource and 'src' in resource:
            print(f"Found history folder for App.jsx: {folder_path} (Resource: {resource})")
            
            # Find the most recent entry that is large enough
            for entry in data.get('entries', []):
                file_id = entry.get('id')
                timestamp = entry.get('timestamp', 0)
                file_path = os.path.join(folder_path, file_id)
                
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    # App.jsx was massive, around 18k lines. That's over 300KB usually.
                    # We will accept anything larger than 100KB to be safe.
                    if size > 100000:
                        print(f"  -> Found valid backup entry: {file_id} (Size: {size} bytes, Time: {timestamp})")
                        if timestamp > best_time:
                            best_time = timestamp
                            best_file = file_path
    except Exception as e:
        # Ignore parse errors
        pass

if best_file:
    print(f"\nSUCCESS! Found the best backup from VS Code history: {best_file}")
    shutil.copy2(best_file, output_file)
    print(f"Successfully recovered to: {output_file}")
else:
    print("\nFAILED: Could not find any App.jsx backup > 100KB in the history.")
