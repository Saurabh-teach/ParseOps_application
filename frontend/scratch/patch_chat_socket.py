import re

with open('c:/Users/saura/ParseOps/frontend/src/components/Chat/useChatSocket.js', 'r', encoding='utf-8') as f:
    content = f.read()

target = """            else if (data.type === 'message_reaction') {"""

replacement = """            else if (data.type === 'workspace_access_lost') {
                window.dispatchEvent(new Event('workspace_access_lost'));
            }
            else if (data.type === 'message_reaction') {"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/frontend/src/components/Chat/useChatSocket.js', 'w', encoding='utf-8') as f:
    f.write(content)
print("useChatSocket.js patched to handle workspace_access_lost")
