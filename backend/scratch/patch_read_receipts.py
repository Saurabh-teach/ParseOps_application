import re

with open('c:/Users/saura/ParseOps/backend/chat/consumers.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add message_read broadcast and handler
db_method_block = """    def mark_message_read(self, user, room_id, message_id):
        try:
            participant = ChatParticipant.objects.get(user=user, room_id=room_id)
            participant.last_read_message_id = message_id
            participant.last_read_at = timezone.now()
            participant.save(update_fields=['last_read_message', 'last_read_at'])
        except ChatParticipant.DoesNotExist:
            pass"""

new_db_method = """    def mark_message_read(self, user, room_id, message_id):
        try:
            participant = ChatParticipant.objects.get(user=user, room_id=room_id)
            participant.last_read_message_id = message_id
            participant.last_read_at = timezone.now()
            participant.save(update_fields=['last_read_message', 'last_read_at'])
            return participant.last_read_at.isoformat()
        except ChatParticipant.DoesNotExist:
            return None"""

if "return participant.last_read_at.isoformat()" not in content:
    content = content.replace(db_method_block, new_db_method)

receive_block = """        elif action == 'mark_read':
            room_id = data.get('room_id')
            message_id = data.get('message_id')
            await self.mark_message_read(self.user, room_id, message_id)"""

new_receive_block = """        elif action == 'mark_read':
            room_id = data.get('room_id')
            message_id = data.get('message_id')
            last_read_at = await self.mark_message_read(self.user, room_id, message_id)
            if last_read_at:
                await self.channel_layer.group_send(
                    f"chat_room_{room_id}",
                    {
                        'type': 'chat_message_read',
                        'room_id': room_id,
                        'user_id': str(self.user.id),
                        'message_id': message_id,
                        'last_read_at': last_read_at
                    }
                )"""

if "chat_message_read" not in content:
    content = content.replace(receive_block, new_receive_block)

handler_block = """    async def user_presence(self, event):"""
new_handler_block = """    async def chat_message_read(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_read',
            'room_id': event['room_id'],
            'user_id': event['user_id'],
            'message_id': event['message_id'],
            'last_read_at': event['last_read_at']
        }))

    async def user_presence(self, event):"""

if "async def chat_message_read" not in content:
    content = content.replace(handler_block, new_handler_block)

with open('c:/Users/saura/ParseOps/backend/chat/consumers.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("consumers.py patched for message_read")
