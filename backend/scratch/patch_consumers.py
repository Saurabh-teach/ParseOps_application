import re

with open('c:/Users/saura/ParseOps/backend/chat/consumers.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """    async def user_typing(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'room_id': event['room_id'],
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'is_typing': event['is_typing']
        }))"""

replacement = """    async def user_typing(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'room_id': event['room_id'],
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'is_typing': event['is_typing']
        }))
        
    async def workspace_access_lost(self, event):
        await self.send(text_data=json.dumps({
            'type': 'workspace_access_lost',
            'org_id': event['org_id']
        }))
        # Close the connection after a short delay to let the message send
        import asyncio
        await asyncio.sleep(0.5)
        await self.close(code=4003)"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/backend/chat/consumers.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("chat/consumers.py patched to handle workspace kick")
