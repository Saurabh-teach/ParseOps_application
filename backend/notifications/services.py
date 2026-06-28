from notifications.models import Notification
from notifications.webpush import send_web_push

class NotificationService:
    @staticmethod
    def send_notification(recipient, n_type, title, message, link=None, organization=None, data=None):
        payload = data or {}
        if link:
            payload['link'] = link
            
        notification = Notification.objects.create(
            user=recipient,
            notification_type=n_type,
            title=title,
            message=message,
            organization=organization,
            data=payload
        )
        
        try:
            send_web_push(
                user=recipient,
                title=title,
                body=message,
                link=link
            )
        except Exception as e:
            print("Failed to send web push:", e)

        # Broadcast via WebSockets
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            from notifications.serializers import NotificationSerializer
            
            channel_layer = get_channel_layer()
            if channel_layer:
                serializer = NotificationSerializer(notification)
                async_to_sync(channel_layer.group_send)(
                    f"user_notifications_{recipient.id}",
                    {
                        "type": "new_notification",
                        "notification": serializer.data
                    }
                )
        except Exception as e:
            print("Failed to broadcast real-time notification:", e)
            
        return notification
