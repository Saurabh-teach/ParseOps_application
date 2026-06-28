import os
import json

history_dir = r"C:\Users\saura\AppData\Roaming\Code\User\History"
found_resources = {}

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
            # Let's count files in folder
            entries = data.get('entries', [])
            largest_size = 0
            for entry in entries:
                p = os.path.join(folder_path, entry.get('id'))
                if os.path.exists(p):
                    largest_size = max(largest_size, os.path.getsize(p))
            found_resources[resource] = {
                'folder': folder,
                'num_entries': len(entries),
                'largest_size': largest_size
            }
    except Exception as e:
        pass

for res, info in found_resources.items():
    print(f"Resource: {res}")
    print(f"  Folder: {info['folder']}, Entries: {info['num_entries']}, Max Size: {info['largest_size']} bytes")
