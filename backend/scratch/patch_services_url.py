import re
from urllib.parse import urlparse

with open('c:/Users/saura/ParseOps/backend/chat/services.py', 'r', encoding='utf-8') as f:
    content = f.read()

url_preview_code = """
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
"""

if "def generate_url_preview" not in content:
    content += url_preview_code
    with open('c:/Users/saura/ParseOps/backend/chat/services.py', 'w', encoding='utf-8') as f:
        f.write(content)
        
print("services.py patched for url_preview")
