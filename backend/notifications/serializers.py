from rest_framework import serializers
from .models import Notification, WebPushSubscription

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'notification_type', 'is_read', 'created_at', 'data']

class WebPushSubscriptionSerializer(serializers.Serializer):
    endpoint = serializers.URLField(max_length=2000)
    p256dh = serializers.CharField(max_length=200)
    auth = serializers.CharField(max_length=200)

