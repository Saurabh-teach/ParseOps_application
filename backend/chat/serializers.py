from rest_framework import serializers
from .models import ChatRoom, ChatParticipant, Message, MessageReaction, MessageAttachment
from users.serializers import UserSerializer
from django.contrib.auth import get_user_model
from django.db.models import Count, Q

User = get_user_model()

class MessageReactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = MessageReaction
        fields = ['id', 'user', 'emoji', 'created_at']


class MessageAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageAttachment
        fields = ['id', 'file', 'file_name', 'file_type', 'file_size', 'created_at']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    reactions = MessageReactionSerializer(many=True, read_only=True)
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    reply_to_preview = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'room', 'sender', 'content', 'file', 'reply_to', 
            'reply_to_preview', 'is_edited', 'is_deleted', 'url_preview',
            'created_at', 'updated_at', 'reactions', 'attachments'
        ]
        read_only_fields = ['room', 'sender', 'is_edited', 'is_deleted']

    def get_reply_to_preview(self, obj):
        if obj.reply_to:
            return {
                'id': obj.reply_to.id,
                'content': obj.reply_to.content,
                'sender_name': obj.reply_to.sender.first_name or obj.reply_to.sender.email
            }
        return None


class ChatParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ChatParticipant
        fields = ['id', 'user', 'role', 'joined_at', 'last_read_message', 'last_read_at']


class ChatRoomSerializer(serializers.ModelSerializer):
    participants = ChatParticipantSerializer(many=True, read_only=True)
    latest_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            'id', 'organization', 'room_type', 'name', 'description', 
            'created_by', 'created_at', 'updated_at', 'participants', 
            'latest_message', 'unread_count'
        ]

    def get_name(self, obj):
        if obj.room_type in ['group', 'task', 'goal']:
            return obj.name
        # For direct chats, return the name of the other person
        request = self.context.get('request')
        if request and request.user:
            other_participant = obj.participants.exclude(user=request.user).first()
            if other_participant:
                u = other_participant.user
                return f"{u.first_name} {u.last_name}".strip() or u.email
        return "Direct Chat"

    def get_latest_message(self, obj):
        msg = obj.messages.order_by('-created_at').first()
        if msg:
            return MessageSerializer(msg).data
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request or not request.user:
            return 0
        try:
            participant = obj.participants.get(user=request.user)
            if participant.last_read_message:
                return obj.messages.filter(created_at__gt=participant.last_read_message.created_at).count()
            else:
                return obj.messages.count()
        except ChatParticipant.DoesNotExist:
            return 0


class CreateGroupChatSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    member_ids = serializers.ListField(
        child=serializers.UUIDField(), allow_empty=False
    )


class CreateDirectChatSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
