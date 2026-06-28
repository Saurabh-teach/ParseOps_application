import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from notifications.models import WebPushSubscription
from pywebpush import webpush, WebPushException
from django.contrib.auth import get_user_model
from django.conf import settings

user_with_sub = WebPushSubscription.objects.first()
if not user_with_sub:
    print("No subscriptions found in DB!")
    exit(0)

user1 = user_with_sub.user
print(f"Testing push for user: {user1.email}")
for sub in WebPushSubscription.objects.filter(user=user1):
    print("Endpoint:", sub.endpoint)

print("Sending push...")
try:
    for sub in WebPushSubscription.objects.filter(user=user1):
        subscription_info = {
            "endpoint": sub.endpoint,
            "keys": {
                "p256dh": sub.p256dh,
                "auth": sub.auth
            }
        }
        res = webpush(
            subscription_info=subscription_info,
            data="Hello from test_push.py",
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": "mailto:admin@parseops.com"}
        )
        print(f"Push response for {sub.endpoint}: {res.status_code} {res.text}")
    print("Push finished!")
except Exception as e:
    print("Exception:", e)
