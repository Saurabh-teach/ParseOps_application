import os
import json

history_dir = r"C:\Users\saura\AppData\Roaming\Code\User\History"
found_entries = []

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
        if 'App.jsx' in resource and 'frontend' in resource:
            for entry in data.get('entries', []):
                file_id = entry.get('id')
                timestamp = entry.get('timestamp')
                source = entry.get('source', '')
                p = os.path.join(folder_path, file_id)
                size = os.path.getsize(p) if os.path.exists(p) else -1
                found_entries.append({
                    'folder': folder,
                    'file_id': file_id,
                    'path': p,
                    'size': size,
                    'source': source,
                    'timestamp': timestamp,
                    'resource': resource
                })
    except Exception as e:
        pass

# Sort by timestamp descending
found_entries.sort(key=lambda x: x['timestamp'] or 0, reverse=True)

# Write to json
with open('found_entries.json', 'w', encoding='utf-8') as out_f:
    json.dump(found_entries, out_f, indent=2, ensure_ascii=False)

print(f"Total entries found: {len(found_entries)}")
for entry in found_entries[:50]:  # Let's print the top 50 entries safely
    safe_source = entry['source'].encode('ascii', 'ignore').decode('ascii')
    print(f"Time: {entry['timestamp']}, Size: {entry['size']}, Folder: {entry['folder']}, ID: {entry['file_id']}, Source: {safe_source}")
