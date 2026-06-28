import re

with open('c:/Users/saura/ParseOps/backend/chat/consumers.py', 'r', encoding='utf-8') as f:
    content = f.read()

import_block = """from django.utils import timezone"""
if import_block not in content:
    content = """from django.utils import timezone\nfrom django.core.cache import cache\n""" + content
else:
    content = content.replace(import_block, "from django.utils import timezone\nfrom django.core.cache import cache")

connect_block = """        await self.accept()"""
new_connect_block = """        await self.accept()
        
        # Track presence
        await self.set_user_online()"""
if "await self.set_user_online()" not in content:
    content = content.replace(connect_block, new_connect_block)

disconnect_block = """                for room_id in self.rooms:
                    await self.channel_layer.group_discard(f"chat_room_{room_id}", self.channel_name)"""
new_disconnect_block = """                for room_id in self.rooms:
                    await self.channel_layer.group_discard(f"chat_room_{room_id}", self.channel_name)
            
            # Track presence
            await self.set_user_offline()"""
if "await self.set_user_offline()" not in content:
    content = content.replace(disconnect_block, new_disconnect_block)

handlers_block = """    async def new_room(self, event):
        await self.send(text_data=json.dumps({
            'type': 'room_created',
            'room': event['room']
        }))"""
new_handlers_block = """    async def new_room(self, event):
        await self.send(text_data=json.dumps({
            'type': 'room_created',
            'room': event['room']
        }))

    async def user_presence(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_presence',
            'user_id': event['user_id'],
            'is_online': event['is_online'],
            'last_seen': event['last_seen']
        }))"""
if "async def user_presence" not in content:
    content = content.replace(handlers_block, new_handlers_block)


db_methods_block = """    @database_sync_to_async
    def get_user_rooms(self, user, org_id):"""
new_db_methods = """    @database_sync_to_async
    def set_user_online(self):
        user_id = str(self.user.id)
        cache_key = f"user_{user_id}_connections"
        connections = cache.get(cache_key, 0)
        cache.set(cache_key, connections + 1, timeout=86400)
        
        if connections == 0:
            self.user.is_online = True
            self.user.save(update_fields=['is_online'])
            # Broadcast to org
            from asgiref.sync import async_to_sync
            async_to_sync(self.channel_layer.group_send)(
                self.org_group_name,
                {
                    'type': 'user_presence',
                    'user_id': user_id,
                    'is_online': True,
                    'last_seen': None
                }
            )

    @database_sync_to_async
    def set_user_offline(self):
        user_id = str(self.user.id)
        cache_key = f"user_{user_id}_connections"
        connections = cache.get(cache_key, 1) - 1
        
        if connections <= 0:
            cache.delete(cache_key)
            self.user.is_online = False
            self.user.last_seen = timezone.now()
            self.user.save(update_fields=['is_online', 'last_seen'])
            
            from asgiref.sync import async_to_sync
            async_to_sync(self.channel_layer.group_send)(
                self.org_group_name,
                {
                    'type': 'user_presence',
                    'user_id': user_id,
                    'is_online': False,
                    'last_seen': self.user.last_seen.isoformat()
                }
            )
        else:
            cache.set(cache_key, connections, timeout=86400)

    @database_sync_to_async
    def get_user_rooms(self, user, org_id):"""

if "def set_user_online" not in content:
    content = content.replace(db_methods_block, new_db_methods)

with open('c:/Users/saura/ParseOps/backend/chat/consumers.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("consumers.py patched for presence")
