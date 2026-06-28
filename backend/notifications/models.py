import uuid
from django.db import models
from django.conf import settings

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('join_request', 'Join Request'),
        ('join_request_approved', 'Join Request Approved'),
        ('join_request_denied', 'Join Request Denied'),
        ('invitation', 'Invitation'),
        ('goal_created', 'Goal Created'),
        ('goal_updated', 'Goal Updated'),
        ('goal_completed', 'Goal Completed'),
        ('goal_due_soon', 'Goal Due Soon'),
        ('task_created', 'Task Created'),
        ('task_updated', 'Task Updated'),
        ('task_deleted', 'Task Deleted'),
        ('task_due_soon', 'Task Due Soon'),
        ('task_assigned', 'Task Assigned'),
        ('task_overdue', 'Task Overdue'),
        ('task_completed', 'Task Completed'),
        ('task_rescheduled', 'Task Rescheduled'),
        ('task_delayed', 'Task Delayed'),
        ('task_queued', 'Task Queued'),
        ('task_scheduled_from_queue', 'Task Scheduled from Queue'),
        ('task_status_changed', 'Task Status Changed'),
        ('extension_requested', 'Extension Requested'),
        ('extension_approved', 'Extension Approved'),
        ('extension_rejected', 'Extension Rejected'),
        ('chat_message', 'New Chat Message'),
        ('chat_mention', 'Mentioned in Chat'),
        ('chat_group_added', 'Added to Group Chat'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField(default=dict, blank=True, null=True)

    class Meta:
        db_table = 'user_notification'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.title} ({'Read' if self.is_read else 'Unread'})"


class WebPushSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='push_subscriptions')
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=200)
    auth = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Push Subscription for {self.user.email}"