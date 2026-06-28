with open('c:/Users/saura/ParseOps/frontend/dist/assets/index-B8bJ4Ru8.js', 'r', encoding='utf-8') as f:
    js = f.read()

keywords = ["Schedule Tasks", "Pending Queue", "Welcome", "Calendar", "Enter Workspace", "Requires Password Change"]

for kw in keywords:
    pos = js.find(kw)
    if pos != -1:
        print(f"Keyword '{kw}' found at position {pos}")
        start = max(0, pos - 200)
        end = min(len(js), pos + 1000)
        print("--- CONTEXT ---")
        context_str = js[start:end].encode('ascii', 'ignore').decode('ascii')
        print(context_str)
        print("---------------\n")
    else:
        print(f"Keyword '{kw}' NOT found")
