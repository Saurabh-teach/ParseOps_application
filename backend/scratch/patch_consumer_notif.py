with open('c:/Users/saura/ParseOps/backend/chat/consumers.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_import = """from .models import ChatRoom, ChatParticipant, Message
from organizations.models import OrganizationMembership"""

new_import = """from .models import ChatRoom, ChatParticipant, Message
from organizations.models import OrganizationMembership
from .services import process_chat_notifications
import threading"""

if old_import in content:
    content = content.replace(old_import, new_import)

old_save = """            if msg.reply_to:
                reply_data = {
                    'id': str(msg.reply_to.id),
                    'content': msg.reply_to.content,
                    'sender_name': msg.reply_to.sender.first_name or msg.reply_to.sender.email
                }
                
            return {"""

new_save = """            if msg.reply_to:
                reply_data = {
                    'id': str(msg.reply_to.id),
                    'content': msg.reply_to.content,
                    'sender_name': msg.reply_to.sender.first_name or msg.reply_to.sender.email
                }
            
            # Fire notifications in background
            threading.Thread(target=process_chat_notifications, args=(msg,)).start()
                
            return {"""

if old_save in content:
    content = content.replace(old_save, new_save)
    with open('c:/Users/saura/ParseOps/backend/chat/consumers.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched consumers.py")
else:
    print("Not found")
