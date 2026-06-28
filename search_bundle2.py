with open('c:/Users/saura/ParseOps/frontend/dist/assets/index-B8bJ4Ru8.js', 'r', encoding='utf-8') as f:
    js = f.read()

keywords = ["/api/users/", "/api/token/", "verify-otp", "ParseOps", "credentials", "otp", "login"]

for kw in keywords:
    pos = js.find(kw)
    if pos != -1:
        print(f"Keyword '{kw}' found at position {pos}")
        # Print 500 characters around the position
        start = max(0, pos - 200)
        end = min(len(js), pos + 1000)
        print("--- CONTEXT ---")
        print(js[start:end])
        print("---------------\n")
    else:
        print(f"Keyword '{kw}' NOT found")
