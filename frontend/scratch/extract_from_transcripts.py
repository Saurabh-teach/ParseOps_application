import os
import json
import glob

brain_dir = r"C:\Users\saura\.gemini\antigravity-ide\brain"
transcripts = []
for root, dirs, files in os.walk(brain_dir):
    for f in files:
        if f == 'transcript.jsonl':
            transcripts.append(os.path.join(root, f))

print(f"Found {len(transcripts)} transcripts.")

best_content = None
best_len = 0
best_time = ""

for t_path in transcripts:
    print(f"Reading {t_path}...")
    try:
        with open(t_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                try:
                    data = json.loads(line)
                except:
                    continue
                
                # Check for tool calls or inputs containing App.jsx
                tool_calls = data.get('tool_calls', [])
                for tc in tool_calls:
                    args = tc.get('args', {})
                    if not args:
                        # Sometimes tool_calls in transcript is a list of dicts, check structure
                        continue
                    
                    content = args.get('CodeContent', '') or args.get('ReplacementContent', '')
                    target_file = args.get('TargetFile', '') or args.get('AbsolutePath', '')
                    
                    if 'App.jsx' in target_file and 'import' in content and 'Dashboard' in content:
                        length = len(content)
                        if length > best_len:
                            best_len = length
                            best_content = content
                            best_time = f"{t_path} (len: {length})"
    except Exception as e:
        print(f"Error reading {t_path}: {e}")

if best_content:
    out_path = r"c:\Users\saura\ParseOps\frontend\src\App_recovered_trans.jsx"
    with open(out_path, 'w', encoding='utf-8') as out:
        out.write(best_content)
    print(f"SUCCESS: Recovered App.jsx from transcripts: {best_time}")
    print(f"Written to {out_path}")
else:
    print("FAILED: Could not find any App.jsx content in transcripts.")
