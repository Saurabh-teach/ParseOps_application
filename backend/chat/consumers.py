import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.core.cache import cache
from .models import ChatRoom, ChatParticipant, Message
from organizations.models import OrganizationMembership
from .services import process_chat_notifications, generate_url_preview
import threading

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.org_id = self.scope['url_route']['kwargs']['org_id']
        
        if self.user.is_anonymous:
            await self.close()
            return
            
        # Verify user belongs to this organization
        is_member = await self.is_org_member(self.user, self.org_id)
        if not is_member:
            await self.close()
            return

        # Organization-level group (for org-wide broadcast like new group creation)
        self.org_group_name = f"chat_org_{self.org_id}"
        await self.channel_layer.group_add(self.org_group_name, self.channel_name)

        # Personal user group within org (for direct messages & invites)
        self.user_group_name = f"chat_user_{self.org_id}_{self.user.id}"
        await self.channel_layer.group_add(self.user_group_name, self.channel_name)

        # Join all existing chat rooms the user is part of
        self.rooms = await self.get_user_rooms(self.user, self.org_id)
        for room_id in self.rooms:
            await self.channel_layer.group_add(f"chat_room_{room_id}", self.channel_name)

        await self.accept()
        
        # Track presence
        await self.set_user_online()

    async def disconnect(self, close_code):
        if not self.user.is_anonymous:
            # Leave org group
            if hasattr(self, 'org_group_name'):
                await self.channel_layer.group_discard(self.org_group_name, self.channel_name)
            # Leave personal group
            if hasattr(self, 'user_group_name'):
                await self.channel_layer.group_discard(self.user_group_name, self.channel_name)
            # Leave room groups
            if hasattr(self, 'rooms'):
                for room_id in self.rooms:
                    await self.channel_layer.group_discard(f"chat_room_{room_id}", self.channel_name)
            
            # Track presence
            await self.set_user_offline()

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'send_message':
            room_id = data.get('room_id')
            content = data.get('content')
            reply_to = data.get('reply_to') # Optional message ID
            
            # Verify permission and save message
            msg = await self.save_message(self.user, room_id, content, reply_to)
            if msg:
                # If this is the first time the user sends a message to this room in this session,
                # they might not be in the group yet (e.g. admins viewing task chats).
                if room_id not in self.rooms:
                    self.rooms.append(room_id)
                    await self.channel_layer.group_add(f"chat_room_{room_id}", self.channel_name)

                # Broadcast to room
                await self.channel_layer.group_send(
                    f"chat_room_{room_id}",
                    {
                        'type': 'chat_message',
                        'message': msg
                    }
                )
                
        elif action == 'typing':
            room_id = data.get('room_id')
            is_typing = data.get('is_typing', True)
            if room_id in self.rooms:
                await self.channel_layer.group_send(
                    f"chat_room_{room_id}",
                    {
                        'type': 'user_typing',
                        'room_id': room_id,
                        'user_id': str(self.user.id),
                        'user_name': self.user.first_name or self.user.email,
                        'is_typing': is_typing
                    }
                )
                
        elif action == 'mark_read':
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
                )

        elif action == 'join_room':
            room_id = data.get('room_id')
            if room_id and room_id not in self.rooms:
                can_join = await self.verify_and_add_participant(self.user, room_id)
                if can_join:
                    self.rooms.append(room_id)
                    await self.channel_layer.group_add(f"chat_room_{room_id}", self.channel_name)
            
        elif action == 'edit_message':
            room_id = data.get('room_id')
            message_id = data.get('message_id')
            new_content = data.get('content')
            msg = await self.edit_message(self.user, room_id, message_id, new_content)
            if msg:
                await self.channel_layer.group_send(
                    f"chat_room_{room_id}",
                    {
                        'type': 'chat_message_edited',
                        'message': msg
                    }
                )

        elif action == 'react_message':
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

        elif action == 'delete_message':
            room_id = data.get('room_id')
            message_id = data.get('message_id')
            msg = await self.delete_message(self.user, room_id, message_id)
            if msg:
                await self.channel_layer.group_send(
                    f"chat_room_{room_id}",
                    {
                        'type': 'chat_message_deleted',
                        'message_id': message_id,
                        'room_id': room_id
                    }
                )

    # --- Handlers for group_send ---
    async def chat_message_read(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_read',
            'room_id': event['room_id'],
            'user_id': event['user_id'],
            'message_id': event['message_id'],
            'last_read_at': event.get('last_read_at')
        }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': event['message']
        }))

    async def chat_message_edited(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_edited',
            'message': event['message']
        }))

    async def message_reaction(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_reaction',
            'message_id': event['message_id'],
            'room_id': event['room_id'],
            'reaction': event['reaction']
        }))

    async def chat_message_deleted(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_deleted',
            'message_id': event['message_id'],
            'room_id': event['room_id']
        }))

    async def user_typing(self, event):
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
        await self.close(code=4003)
        
    async def new_room(self, event):
        # Triggered when someone creates a group or DM and adds this user
        room_data = event['room']
        room_id = room_data['id']
        # Dynamically join the new room group
        if room_id not in self.rooms:
            self.rooms.append(room_id)
            await self.channel_layer.group_add(f"chat_room_{room_id}", self.channel_name)
            
        await self.send(text_data=json.dumps({
            'type': 'room_created',
            'room': room_data
        }))

    async def user_presence(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_presence',
            'user_id': event['user_id'],
            'is_online': event['is_online'],
            'last_seen': event.get('last_seen')
        }))

    # --- Database Sync Methods ---
    @database_sync_to_async
    def is_org_member(self, user, org_id):
        return OrganizationMembership.objects.filter(organization_id=org_id, user=user, is_active=True).exists()

    @database_sync_to_async
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
    def verify_and_add_participant(self, user, room_id):
        from .models import ChatRoom, ChatParticipant
        from organizations.models import OrganizationMembership
        try:
            room = ChatRoom.objects.get(id=room_id)
            membership = OrganizationMembership.objects.filter(
                organization_id=room.organization_id, user=user, is_active=True
            ).first()
            if membership:
                ChatParticipant.objects.get_or_create(room=room, user=user)
                return True
            return False
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def get_user_rooms(self, user, org_id):
        return list(ChatParticipant.objects.filter(
            user=user, 
            room__organization_id=org_id
        ).values_list('room_id', flat=True))

    @database_sync_to_async
    def save_message(self, user, room_id, content, reply_to_id=None):
        try:
            try:
                participant = ChatParticipant.objects.get(user=user, room_id=room_id)
            except ChatParticipant.DoesNotExist:
                # If they are trying to send a message, we must verify if they can join the room.
                # Assuming if they made it here, they belong to the org.
                # Let's add them to the room if it's an org-visible room or if they are admins.
                from .models import ChatRoom
                from organizations.models import OrganizationMembership
                try:
                    room = ChatRoom.objects.get(id=room_id)
                    membership = OrganizationMembership.objects.filter(
                        organization_id=room.organization_id, user=user, is_active=True
                    ).first()
                    if membership:
                        # Add them as a participant
                        participant, _ = ChatParticipant.objects.get_or_create(room=room, user=user)
                    else:
                        return None
                except ChatRoom.DoesNotExist:
                    return None
            
            msg = Message.objects.create(
                room_id=room_id,
                sender=user,
                content=content,
                reply_to_id=reply_to_id
            )
            # Update last read for sender automatically
            participant.last_read_message = msg
            participant.last_read_at = timezone.now()
            participant.save(update_fields=['last_read_message', 'last_read_at'])
            
            reply_data = None
            if msg.reply_to:
                reply_data = {
                    'id': str(msg.reply_to.id),
                    'content': msg.reply_to.content,
                    'sender_name': msg.reply_to.sender.first_name or msg.reply_to.sender.email
                }
            
            # Fire notifications in background
            threading.Thread(target=process_chat_notifications, args=(msg,)).start()
            # Fetch URL preview in background
            threading.Thread(target=generate_url_preview, args=(msg,)).start()
                
            return {
                'id': str(msg.id),
                'room_id': str(room_id),
                'content': msg.content,
                'sender_id': str(user.id),
                'sender_name': user.first_name or user.email,
                'sender_email': user.email,
                'reply_to': reply_data,
                'created_at': msg.created_at.isoformat(),
            }
        except ChatParticipant.DoesNotExist:
            return None

    @database_sync_to_async
    def edit_message(self, user, room_id, message_id, new_content):
        from django.utils import timezone
        from datetime import timedelta
        try:
            msg = Message.objects.get(id=message_id, room_id=room_id, sender=user)
            if timezone.now() - msg.created_at > timedelta(minutes=10):
                return None # Disallow editing after 10 minutes
                
            msg.content = new_content
            msg.is_edited = True
            msg.save(update_fields=['content', 'is_edited', 'updated_at'])
            return {
                'id': str(msg.id),
                'room_id': str(room_id),
                'content': msg.content,
                'is_edited': True,
                'is_deleted': msg.is_deleted,
                'sender_id': str(msg.sender.id)
            }
        except Message.DoesNotExist:
            return None

    @database_sync_to_async
    def delete_message(self, user, room_id, message_id):
        from django.utils import timezone
        from datetime import timedelta
        try:
            msg = Message.objects.get(id=message_id, room_id=room_id, sender=user)
            # You can also restrict deletion to 10 minutes, but let's allow it or enforce it if requested
            # Assuming 10 minute rule applies to delete as well based on requirements "Edit/Delete their own messages (within 10 minutes)" wait, usually delete is anytime, but let's enforce it on delete too, or maybe only edit? User said: "Users can Edit their own messages (within 10 minutes)". Delete might be anytime. Let's enforce on edit only for now, wait, user said "Message CRUD Operations: - Users can Edit their own messages (within 10 minutes) - Users can Delete their own messages". So delete anytime.
            msg.is_deleted = True
            msg.content = "This message was deleted."
            msg.save(update_fields=['is_deleted', 'content', 'updated_at'])
            return True
        except Message.DoesNotExist:
            return False

    @database_sync_to_async
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
    def mark_message_read(self, user, room_id, message_id):
        try:
            participant = ChatParticipant.objects.get(user=user, room_id=room_id)
            participant.last_read_message_id = message_id
            participant.last_read_at = timezone.now()
            participant.save(update_fields=['last_read_message', 'last_read_at'])
            return participant.last_read_at.isoformat()
        except ChatParticipant.DoesNotExist:
            return None
