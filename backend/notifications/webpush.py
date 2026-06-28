# notifications/webpush.py
import json
from pywebpush import webpush, WebPushException
from django.conf import settings
from .models import WebPushSubscription

def send_web_push(user, title, body, link=None, icon="/icon.png"):
    """
    Sends a Web Push Notification to all active subscriptions of a specific user.
    """
    # 1. Prepare the payload that the browser Service Worker will receive
    payload = json.dumps({
        "title": title,
        "body": body,
        "icon": icon,
        "url": link or "/",
    })

    # 2. Get all browser subscriptions for this user
    subscriptions = WebPushSubscription.objects.filter(user=user)

    if not subscriptions.exists():
        return

    # 3. Send the push notification to each subscription endpoint
    for sub in subscriptions:
        subscription_info = {
            "endpoint": sub.endpoint,
            "keys": {
                "p256dh": sub.p256dh,
                "auth": sub.auth
            }
        }

        try:
            webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={
                    "sub": f"mailto:{getattr(settings, 'VAPID_ADMIN_EMAIL', 'admin@parseops.com')}"
                }
            )
        except WebPushException as ex:
            # If the browser unsubscribed or the token expired, delete the old subscription
            if ex.response and ex.response.status_code in [404, 410]:
                sub.delete()
            else:
                print("Web Push Error:", repr(ex))
