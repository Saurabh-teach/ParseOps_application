import json
import os

with open('found_entries.json', 'r', encoding='utf-8') as f:
    entries = json.load(f)

print(f"Loaded {len(entries)} entries.")

# Find entries where the 'source' contains react code or is very long
for i, entry in enumerate(entries):
    src = entry.get('source', '') or ''
    if len(src) > 1000:
        print(f"[{i}] Folder: {entry['folder']}, ID: {entry['file_id']}, Source length: {len(src)} chars, Time: {entry['timestamp']}")
        # Let's save the first one that is very long
        out_name = f"extracted_src_{entry['folder']}_{entry['file_id']}.txt"
        with open(out_name, 'w', encoding='utf-8') as out_f:
            out_f.write(src)
        print(f"  -> Saved source field to {out_name}")
