import os
import json

history_dir = r"c:\Users\saura\AppData\Roaming\Code\User\History"
out_path = r"c:\Users\saura\ParseOps\frontend\scratch\history_out.txt"

with open(out_path, 'w', encoding='utf-8') as out:
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
            if 'App.jsx' in resource:
                out.write(f"Resource: {resource}\n")
                out.write(f"Folder: {folder}\n")
                for entry in data.get('entries', []):
                    file_id = entry.get('id')
                    timestamp = entry.get('timestamp')
                    source = entry.get('source', '')
                    p = os.path.join(folder_path, file_id)
                    size = os.path.getsize(p) if os.path.exists(p) else -1
                    out.write(f"  Entry: {file_id}, Size: {size}, Source: {source}, Timestamp: {timestamp}\n")
        except Exception as e:
            out.write(f"Error in {folder}: {e}\n")

print("Done scanning history!")
