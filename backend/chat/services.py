import json
from django.conf import settings
from notifications.models import Notification

def process_chat_notifications(message_obj):
    """
    Sends in-app notifications to all 
    room participants except the sender.
    """
    room = message_obj.room
    sender = message_obj.sender
    
    # Get all participants except the sender
    participants = room.participants.exclude(user=sender).select_related('user')
    
    for participant in participants:
        receiver = participant.user
        
        # Room naming logic for the notification
        if room.room_type == 'group':
            title = f"New message in {room.name}"
            body = f"{sender.first_name or sender.email}: {message_obj.content[:40]}..."
        else:
            title = f"Message from {sender.first_name or sender.email}"
            body = message_obj.content[:50] + "..." if message_obj.content else "Sent an attachment"

        # 1. Create In-App Notification (Badge/Bell)
        notif = Notification.objects.create(
            user=receiver,
            organization=room.organization,
            title=title,
            message=body,
            notification_type='chat_message',
            data={'room_id': str(room.id), 'message_id': str(message_obj.id)}
        )
        
        # 2. Send Web Push Notification
        try:
            from notifications.webpush import send_web_push
            # Create a link that navigates to the chat room
            link = f"/workspace/chat"
            send_web_push(
                user=receiver,
                title=title,
                body=body,
                link=link
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to send web push for chat message: {e}")
        


import re
import requests
from bs4 import BeautifulSoup
from .models import Message

def get_url_from_text(text):
    if not text:
        return None
    urls = re.findall(r'(https?://[^\s]+)', text)
    return urls[0] if urls else None

def generate_url_preview(msg):
    url = get_url_from_text(msg.content)
    if not url:
        return

    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.find('meta', property='og:title')
            description = soup.find('meta', property='og:description')
            image = soup.find('meta', property='og:image')
            
            if not title:
                title = soup.find('title')
                
            preview_data = {
                'url': url,
                'title': title.get('content', '') if title and title.name == 'meta' else (title.string if title else url),
                'description': description.get('content', '') if description else '',
                'image': image.get('content', '') if image else ''
            }
            
            msg.url_preview = preview_data
            msg.save(update_fields=['url_preview'])
            
            # Broadcast the updated message with url_preview to the channel
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            from .serializers import MessageSerializer
            
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"chat_room_{msg.room.id}",
                {
                    'type': 'chat_message_edited',  # we can reuse the edit event to update the message
                    'message': MessageSerializer(msg).data
                }
            )
            
    except Exception as e:
        print(f"Error fetching URL preview: {e}")
