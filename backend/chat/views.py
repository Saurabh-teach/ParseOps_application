from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from .models import ChatRoom, ChatParticipant, Message, MessageReaction, MessageAttachment
from .serializers import (
    ChatRoomSerializer, MessageSerializer, CreateGroupChatSerializer, 
    CreateDirectChatSerializer
)
from organizations.models import Organization, OrganizationMembership
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .services import process_chat_notifications, generate_url_preview
import threading

User = get_user_model()

class IsOrganizationMember(permissions.BasePermission):
    def has_permission(self, request, view):
        org_slug = view.kwargs.get('org_slug')
        if not org_slug:
            return False
        return OrganizationMembership.objects.filter(
            organization__slug=org_slug, user=request.user, is_active=True
        ).exists()


class ChatRoomViewSet(viewsets.ModelViewSet):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizationMember]

    def get_queryset(self):
        org_slug = self.kwargs.get('org_slug')
        membership = OrganizationMembership.objects.filter(
            organization__slug=org_slug, user=self.request.user, is_active=True
        ).first()

        if membership and membership.role in ['owner', 'admin']:
            # Owner/Admin can see all chats
            return ChatRoom.objects.filter(organization__slug=org_slug).prefetch_related('participants__user').distinct()
        
        # Regular members see rooms they participate in, OR rooms linked to org-visible goals/tasks
        return ChatRoom.objects.filter(
            Q(organization__slug=org_slug) & (
                Q(participants__user=self.request.user) |
                Q(goal__sharing_option='organization') |
                Q(goal__visibility_type='organization') |
                Q(task__visibility_type='organization')
            )
        ).prefetch_related('participants__user').distinct()

    def get_organization(self):
        org_slug = self.kwargs.get('org_slug')
        return get_object_or_404(Organization, slug=org_slug)

    @action(detail=False, methods=['post'])
    def create_direct(self, request, org_slug=None):
        org = self.get_organization()
        serializer = CreateDirectChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        target_user_id = serializer.validated_data['user_id']
        target_user = get_object_or_404(User, id=target_user_id)
        
        # Verify target is in org
        if not OrganizationMembership.objects.filter(organization=org, user=target_user, is_active=True).exists():
            return Response({"detail": "User is not in this organization."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if direct room already exists
        existing_room = ChatRoom.objects.filter(
            organization=org, 
            room_type='direct',
            participants__user=request.user
        ).filter(
            participants__user=target_user
        ).annotate(
            p_count=Count('participants')
        ).filter(p_count=2).first()
        
        if existing_room:
            return Response(ChatRoomSerializer(existing_room, context={'request': request}).data)

        # Create new direct room
        room = ChatRoom.objects.create(organization=org, room_type='direct')
        ChatParticipant.objects.create(room=room, user=request.user)
        ChatParticipant.objects.create(room=room, user=target_user)
        
        # Notify target user via channels
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_user_{org.id}_{target_user.id}",
            {
                'type': 'new_room',
                'room': ChatRoomSerializer(room, context={'request': request}).data
            }
        )

        return Response(ChatRoomSerializer(room, context={'request': request}).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def create_group(self, request, org_slug=None):
        org = self.get_organization()
        serializer = CreateGroupChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        member_ids = serializer.validated_data['member_ids']
        if request.user.id not in member_ids:
            member_ids.append(request.user.id)
            
        users = User.objects.filter(id__in=member_ids)
        
        room = ChatRoom.objects.create(
            organization=org, 
            room_type='group',
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description', ''),
            created_by=request.user
        )
        
        participants = []
        for user in users:
            role = 'admin' if user == request.user else 'member'
            participants.append(ChatParticipant(room=room, user=user, role=role))
            
        ChatParticipant.objects.bulk_create(participants)
        
        room_data = ChatRoomSerializer(room, context={'request': request}).data
        
        # Notify users via channels
        channel_layer = get_channel_layer()
        for user in users:
            if user != request.user:
                async_to_sync(channel_layer.group_send)(
                    f"chat_user_{org.id}_{user.id}",
                    {'type': 'new_room', 'room': room_data}
                )

        return Response(room_data, status=status.HTTP_201_CREATED)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizationMember]

    def get_queryset(self):
        room_id = self.kwargs.get('room_pk')
        org_slug = self.kwargs.get('org_slug')
        membership = OrganizationMembership.objects.filter(
            organization__slug=org_slug, user=self.request.user, is_active=True
        ).first()

        if membership and membership.role in ['owner', 'admin']:
            return Message.objects.filter(room_id=room_id).select_related('sender').prefetch_related('reactions')
            
        return Message.objects.filter(
            Q(room_id=room_id) & (
                Q(room__participants__user=self.request.user) |
                Q(room__goal__sharing_option='organization') |
                Q(room__goal__visibility_type='organization') |
                Q(room__task__visibility_type='organization')
            )
        ).select_related('sender').prefetch_related('reactions')

    def perform_create(self, serializer):
        room_id = self.kwargs.get('room_pk')
        org_slug = self.kwargs.get('org_slug')
        
        membership = OrganizationMembership.objects.filter(
            organization__slug=org_slug, user=self.request.user, is_active=True
        ).first()
        
        if membership and membership.role in ['owner', 'admin']:
            room = get_object_or_404(ChatRoom, id=room_id, organization__slug=org_slug)
            # Make sure admin is a participant if they chat
            ChatParticipant.objects.get_or_create(room=room, user=self.request.user)
        else:
            room = get_object_or_404(
                ChatRoom.objects.filter(
                    Q(id=room_id) & (
                        Q(participants__user=self.request.user) |
                        Q(goal__sharing_option='organization') |
                        Q(goal__visibility_type='organization') |
                        Q(task__visibility_type='organization')
                    )
                )
            )
            # If they chat, they become a participant
            ChatParticipant.objects.get_or_create(room=room, user=self.request.user)
        msg = serializer.save(room=room, sender=self.request.user)
        
        files = self.request.FILES.getlist('files')
        for f in files:
            MessageAttachment.objects.create(
                message=msg,
                file=f,
                file_name=f.name,
                file_type=f.content_type,
                file_size=f.size
            )
        
        # Update last read for sender
        participant = ChatParticipant.objects.get(room=room, user=self.request.user)
        participant.last_read_message = msg
        participant.save(update_fields=['last_read_message'])
        
        # Fire notifications in background
        threading.Thread(target=process_chat_notifications, args=(msg,)).start()
        
        # Refresh msg from db to load attachments
        msg.refresh_from_db()

        # Broadcast via Channels
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_room_{room.id}",
            {
                'type': 'chat_message',
                'message': MessageSerializer(msg).data
            }
        )
