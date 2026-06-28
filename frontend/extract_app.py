import json
import os

transcript_path = r'C:\Users\saura\.gemini\antigravity-ide\brain\5d078dc2-4f58-46b8-a3a8-d2ddec4844cc\.system_generated\logs\transcript.jsonl'
output_path = r'c:\Users\saura\ParseOps\frontend\src\App_recovered.jsx'

best_content = ""
best_len = 0

with open(transcript_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            obj = json.loads(line)
        except:
            continue
            
        if obj.get('type') == 'USER_INPUT':
            content = obj.get('content', '')
            if 'import React' in content and 'ContextualChat' in content:
                if len(content) > best_len:
                    best_len = len(content)
                    best_content = content

if best_content:
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(best_content)
    print(f"Recovered App.jsx with {best_len} characters to {output_path}")
else:
    print("Could not find App.jsx in the transcript.")
