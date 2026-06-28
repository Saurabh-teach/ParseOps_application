with open('c:/Users/saura/ParseOps/backend/config/urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_code = """    path("api/", include("tasks.urls")),"""
new_code = """    path("api/", include("tasks.urls")),
    path("api/", include("chat.urls")),"""

if old_code in content and "chat.urls" not in content:
    content = content.replace(old_code, new_code)
    with open('c:/Users/saura/ParseOps/backend/config/urls.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched urls.py")
else:
    print("Not found or already patched")
