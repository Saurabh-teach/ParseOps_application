import json

with open('found_entries.json', 'r', encoding='utf-8') as f:
    entries = json.load(f)

# Sort by size descending
by_size = sorted(entries, key=lambda x: x['size'], reverse=True)

print("All history files and their sizes:")
for i, entry in enumerate(by_size):
    print(f"[{i}] Folder: {entry['folder']}, ID: {entry['file_id']}, Size: {entry['size']} bytes, Time: {entry['timestamp']}, Resource: {entry['resource']}")
