with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("visibility_type: 'organization'", "visibility_type: 'specific'")
content = content.replace("sharing_option: 'organization'", "sharing_option: 'specific'")

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
