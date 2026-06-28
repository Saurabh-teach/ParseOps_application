import re

with open('c:/Users/saura/ParseOps/backend/chat/consumers.py', 'r', encoding='utf-8') as f:
    content = f.read()

action_block = """        elif action == 'delete_message':"""
new_action_block = """        elif action == 'react_message':
            room_id = data.get('room_id')
            message_id = data.get('message_id')
            emoji = data.get('emoji')
            reaction = await self.react_to_message(self.user, room_id, message_id, emoji)
            if reaction:
                await self.channel_layer.group_send(
                    f"chat_room_{room_id}",
                    {
                        'type': 'message_reaction',
                        'message_id': message_id,
                        'room_id': room_id,
                        'reaction': reaction
                    }
                )

        elif action == 'delete_message':"""
if "elif action == 'react_message':" not in content:
    content = content.replace(action_block, new_action_block)


handler_block = """    async def chat_message_deleted(self, event):"""
new_handler_block = """    async def message_reaction(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_reaction',
            'message_id': event['message_id'],
            'room_id': event['room_id'],
            'reaction': event['reaction']
        }))

    async def chat_message_deleted(self, event):"""
if "async def message_reaction" not in content:
    content = content.replace(handler_block, new_handler_block)


db_method_block = """    @database_sync_to_async
    def mark_message_read(self, user, room_id, message_id):"""
new_db_method = """    @database_sync_to_async
    def react_to_message(self, user, room_id, message_id, emoji):
        from .models import MessageReaction
        try:
            msg = Message.objects.get(id=message_id, room_id=room_id)
            reaction, created = MessageReaction.objects.get_or_create(
                message=msg,
                user=user,
                emoji=emoji
            )
            # If user clicked the same emoji again, maybe toggle it?
            # WhatsApp adds it. If we want toggle, we can delete it.
            if not created:
                reaction.delete()
                return {'emoji': emoji, 'user_id': str(user.id), 'deleted': True}
                
            return {
                'id': str(reaction.id),
                'emoji': emoji,
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                },
                'created_at': reaction.created_at.isoformat()
            }
        except Message.DoesNotExist:
            return None

    @database_sync_to_async
    def mark_message_read(self, user, room_id, message_id):"""
if "def react_to_message" not in content:
    content = content.replace(db_method_block, new_db_method)

with open('c:/Users/saura/ParseOps/backend/chat/consumers.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("consumers.py patched for reactions")
