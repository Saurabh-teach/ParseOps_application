import json

with open('found_entries.json', 'r', encoding='utf-8') as f:
    entries = json.load(f)

# Filter entries by file size
filtered = [e for e in entries if 5000 <= e['size'] <= 100000]

print(f"Found {len(filtered)} history entries between 5KB and 100KB:")
for i, entry in enumerate(filtered):
    print(f"[{i}] Folder: {entry['folder']}, ID: {entry['file_id']}, Size: {entry['size']} bytes, Time: {entry['timestamp']}, Src: {str(entry['source'])[:80]}")
