with open('c:/Users/saura/ParseOps/backend/chat/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("organization__name=org_slug", "organization__slug=org_slug")
content = content.replace("name=org_slug", "slug=org_slug")

with open('c:/Users/saura/ParseOps/backend/chat/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched org_slug in views")
