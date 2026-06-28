import re

with open('c:/Users/saura/ParseOps/backend/chat/services.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """        # 1. Create In-App Notification (Badge/Bell)
        notif = Notification.objects.create(
            user=receiver,
            organization=room.organization,
            title=title,
            message=body,
            notification_type='chat_message',
            data={'room_id': str(room.id), 'message_id': str(message_obj.id)}
        )"""

replacement = """        # 1. Create In-App Notification (Badge/Bell)
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
            logging.getLogger(__name__).error(f"Failed to send web push for chat message: {e}")"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/backend/chat/services.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("chat/services.py patched to send web push notifications")
