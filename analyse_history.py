import json

with open('found_entries.json', 'r', encoding='utf-8') as f:
    entries = json.load(f)

print(f"Total entries loaded: {len(entries)}")

# Sort by size descending
by_size = sorted(entries, key=lambda x: x['size'], reverse=True)

print("\nTop 20 largest files in history:")
for i, entry in enumerate(by_size[:20]):
    print(f"[{i}] Folder: {entry['folder']}, ID: {entry['file_id']}, Size: {entry['size']} bytes, Time: {entry['timestamp']}, Src: {str(entry['source'])[:80]}")
