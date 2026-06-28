import uuid
from django.db import models
from django.conf import settings
from organizations.models import Organization

class ChatRoom(models.Model):
    ROOM_TYPES = (
        ('direct', 'Direct Message'),
        ('group', 'Group Chat'),
        ('goal', 'Goal Chat'),
        ('task', 'Task Chat'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='chat_rooms')
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES)
    name = models.CharField(max_length=255, blank=True, null=True)  # Only for group chats
    description = models.TextField(blank=True, null=True)  # Only for group chats
    goal = models.OneToOneField('goals.Goals', on_delete=models.CASCADE, null=True, blank=True, related_name='chat_room')
    task = models.OneToOneField('tasks.Task', on_delete=models.CASCADE, null=True, blank=True, related_name='chat_room')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_rooms'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_room'
        ordering = ['-updated_at']

    def __str__(self):
        if self.room_type == 'group':
            return f"Group: {self.name} ({self.organization.name})"
        return f"Direct: {self.id} ({self.organization.name})"


class ChatParticipant(models.Model):
    ROLE_CHOICES = (
        ('member', 'Member'),
        ('admin', 'Admin'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_participants')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_message = models.ForeignKey(
        'Message', on_delete=models.SET_NULL, null=True, blank=True, related_name='read_by'
    )
    last_read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_participant'
        unique_together = ('room', 'user')

    def __str__(self):
        return f"{self.user.email} in {self.room}"


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='chat_files/%Y/%m/%d/', blank=True, null=True)
    reply_to = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies'
    )
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    url_preview = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_message'
        ordering = ['created_at']

    def __str__(self):
        return f"Message by {self.sender.email} at {self.created_at}"


class MessageReaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='message_reactions')
    emoji = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_message_reaction'
        unique_together = ('message', 'user', 'emoji')

    def __str__(self):
        return f"{self.emoji} by {self.user.email} on {self.message_id}"

class MessageAttachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='chat_attachments/%Y/%m/%d/')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100, blank=True, null=True)
    file_size = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_message_attachment'

    def __str__(self):
        return f"{self.file_name} attached to {self.message_id}"
