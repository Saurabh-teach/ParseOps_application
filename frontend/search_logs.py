import os
import re
import json

log_path = r"C:\Users\saura\.gemini\antigravity-ide\brain\5d078dc2-4f58-46b8-a3a8-d2ddec4844cc\.system_generated\logs\transcript.jsonl"

if not os.path.exists(log_path):
    import glob
    files = glob.glob(r"C:\Users\saura\.gemini\antigravity-ide\brain\**\transcript.jsonl", recursive=True)
    if files:
        log_path = files[0]
    else:
        print("Log file not found.")
        sys.exit(1)

print(f"Searching {log_path}...")

# Let's find matches and extract the surrounding lines
matches = []
with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if "connecting_sso" in line:
            # Try parsing as JSON to get content safely
            try:
                data = json.loads(line)
                content = str(data.get("content", "")) + str(data.get("tool_calls", ""))
            except Exception:
                content = line
            
            # Find connecting_sso and extract around it
            for match in re.finditer(r"if\s*\(\s*view\s*===\s*'connecting_sso'\s*\)", content):
                start = max(0, match.start() - 200)
                end = min(len(content), match.end() + 2000)
                snippet = content[start:end]
                if snippet not in matches:
                    matches.append(snippet)

print(f"Found {len(matches)} unique code snippets in logs.")
for idx, m in enumerate(matches[:5]):
    print(f"\n--- Snippet {idx+1} ---")
    print(m)
