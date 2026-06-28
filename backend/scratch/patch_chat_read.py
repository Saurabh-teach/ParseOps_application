import re

with open('c:/Users/saura/ParseOps/backend/chat/consumers.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """    async def chat_message(self, event):"""

replacement = """    async def chat_message_read(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_read',
            'room_id': event['room_id'],
            'user_id': event['user_id'],
            'message_id': event['message_id'],
            'last_read_at': event.get('last_read_at')
        }))

    async def chat_message(self, event):"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/backend/chat/consumers.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("consumers.py patched to add chat_message_read handler")
