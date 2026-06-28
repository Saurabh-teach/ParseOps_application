import re

with open('c:/Users/saura/ParseOps/backend/chat/services.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove imports
import_block = """from pywebpush import webpush, WebPushException
from django.conf import settings
from notifications.models import Notification, WebPushSubscription"""
new_import_block = """from django.conf import settings
from notifications.models import Notification"""
content = content.replace(import_block, new_import_block)

# Remove Web Push logic
webpush_block = """        # 2. Trigger Browser Web Push
        try:
            vapid_private_key = getattr(settings, 'VAPID_PRIVATE_KEY', None)
            vapid_admin_email = getattr(settings, 'VAPID_ADMIN_EMAIL', 'admin@parseops.com')
            
            if vapid_private_key:
                subs = WebPushSubscription.objects.filter(user=receiver)
                payload = json.dumps({
                    "title": title,
                    "body": body,
                    "url": f"/{room.organization.name}/chat/{room.id}",
                    "icon": "/parseops-logo.png"
                })
                
                for sub in subs:
                    try:
                        webpush(
                            subscription_info={
                                "endpoint": sub.endpoint,
                                "keys": {
                                    "p256dh": sub.p256dh,
                                    "auth": sub.auth
                                }
                            },
                            data=payload,
                            vapid_private_key=vapid_private_key,
                            vapid_claims={"sub": f"mailto:{vapid_admin_email}"}
                        )
                    except WebPushException as e:
                        # Clean up expired/unsubscribed browser endpoints
                        if e.response and e.response.status_code in [404, 410]:
                            sub.delete()
        except Exception as e:
            print(f"Failed to send Web Push: {e}")"""
content = content.replace(webpush_block, "")

# Remove "and Web Push notifications" from docstring
docstring_block = """    Sends in-app notifications and Web Push notifications to all 
    room participants except the sender."""
new_docstring_block = """    Sends in-app notifications to all 
    room participants except the sender."""
content = content.replace(docstring_block, new_docstring_block)

with open('c:/Users/saura/ParseOps/backend/chat/services.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Removed WebPush from services.py")
