import re

with open('c:/Users/saura/ParseOps/backend/chat/consumers.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """    @database_sync_to_async
    @database_sync_to_async
    def is_org_member(self, user, org_id):"""

replacement = """    @database_sync_to_async
    def is_org_member(self, user, org_id):"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/backend/chat/consumers.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("consumers.py fixed double decorator")
