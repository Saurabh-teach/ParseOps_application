import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
            return
            
        # Personal user group for all system notifications
        self.user_group_name = f"user_notifications_{self.user.id}"
        await self.channel_layer.group_add(self.user_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if not self.user.is_anonymous and hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(self.user_group_name, self.channel_name)

    async def receive(self, text_data):
        # We don't necessarily need to receive much from the client for notifications,
        # but we could handle mark_read events here if we wanted to avoid HTTP requests.
        pass

    async def new_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'notification': event['notification']
        }))
