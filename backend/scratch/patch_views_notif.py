with open('c:/Users/saura/ParseOps/backend/chat/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_import = """from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync"""

new_import = """from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .services import process_chat_notifications
import threading"""

if old_import in content:
    content = content.replace(old_import, new_import)

old_save = """        # Broadcast via Channels
        channel_layer = get_channel_layer()"""

new_save = """        # Fire notifications in background
        threading.Thread(target=process_chat_notifications, args=(msg,)).start()
        
        # Broadcast via Channels
        channel_layer = get_channel_layer()"""

if old_save in content:
    content = content.replace(old_save, new_save)
    with open('c:/Users/saura/ParseOps/backend/chat/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched views.py")
else:
    print("Not found")
