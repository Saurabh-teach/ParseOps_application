from rest_framework import serializers
from .models import (
    Organization, 
    OrganizationMembership, 
    OrganizationJoinRequest, 
    OrganizationInvitation
)
from django.contrib.auth import get_user_model

User = get_user_model()

from users.serializers import UserSerializer

class MemberDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    is_on_leave = serializers.SerializerMethodField()
    leave_details = serializers.SerializerMethodField()
    is_busy = serializers.SerializerMethodField()
    active_task_title = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationMembership
        fields = [
            'id', 'organization', 'user', 'user_id', 'email', 'role', 
            'custom_permissions', 'joined_at', 'is_on_leave', 'leave_details',
            'is_busy', 'active_task_title'
        ]
        read_only_fields = ['id', 'organization', 'joined_at']

    def get_is_busy(self, obj):
        from tasks.models import Task
        return Task.objects.filter(
            assignee=obj.user,
            organization=obj.organization,
            status='in_progress',
            is_deleted=False
        ).exists()

    def get_active_task_title(self, obj):
        from tasks.models import Task
        task = Task.objects.filter(
            assignee=obj.user,
            organization=obj.organization,
            status='in_progress',
            is_deleted=False
        ).first()
        return task.title if task else None

    def get_is_on_leave(self, obj):
        from users.models import LeaveRequest
        from django.utils import timezone
        today = timezone.now().date()
        return LeaveRequest.objects.filter(
            user=obj.user,
            organization=obj.organization,
            status='Approved',
            start_date__lte=today,
            end_date__gte=today
        ).exists()

    def get_leave_details(self, obj):
        from users.models import LeaveRequest
        from django.utils import timezone
        today = timezone.now().date()
        leave = LeaveRequest.objects.filter(
            user=obj.user,
            organization=obj.organization,
            status='Approved',
            start_date__lte=today,
            end_date__gte=today
        ).first()
        if leave:
            return {
                'start_date': leave.start_date.isoformat(),
                'end_date': leave.end_date.isoformat(),
                'leave_type': leave.leave_type,
                'reason': leave.reason
            }
        return None

class OrganizationSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    my_status = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'slug', 'description', 'logo', 'owner', 'owner_email',
            'is_active', 'is_public', 'member_count', 'created_by_email', 'my_status'
        ]
        read_only_fields = ['id', 'slug', 'owner', 'owner_email', 'is_active', 'member_count', 'created_by_email', 'my_status']

    def get_my_status(self, obj):
        user = self.context.get('request').user
        if not user or user.is_anonymous:
            return None
            
        # Check membership
        membership = OrganizationMembership.objects.filter(organization=obj, user=user, is_active=True).first()
        if membership:
            return {
                'type': 'member', 
                'role': membership.role,
                'custom_permissions': membership.custom_permissions or {}
            }
            
        # Check pending invitation
        from django.utils import timezone
        invitation = OrganizationInvitation.objects.filter(
            organization=obj, 
            email__iexact=user.email, 
            status='pending',
            expires_at__gt=timezone.now()
        ).first()
        if invitation:
            return {
                'type': 'invitation',
                'status': 'pending',
                'id': str(invitation.id),
                'role': invitation.role,
                'invited_by': invitation.invited_by.email if invitation.invited_by else None
            }
            
        # Check pending request
        request = OrganizationJoinRequest.objects.filter(organization=obj, user=user, status='pending').first()
        if request:
            return {'type': 'request', 'status': 'pending', 'role': request.requested_role}
            
        return None

class JoinRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationJoinRequest
        fields = ['organization', 'requested_role', 'message']

    def validate(self, data):
        user = self.context['request'].user
        org = data['organization']
        
        if OrganizationMembership.objects.filter(organization=org, user=user, is_active=True).exists():
            raise serializers.ValidationError("You are already a member of this workspace.")
            
        if OrganizationJoinRequest.objects.filter(organization=org, user=user, status='pending').exists():
            raise serializers.ValidationError("You already have a pending request for this workspace.")
            
        return data

class InvitationSerializer(serializers.ModelSerializer):
    invited_by_email = serializers.EmailField(source='invited_by.email', read_only=True)

    class Meta:
        model = OrganizationInvitation
        fields = ['id', 'email', 'role', 'token', 'status', 'message', 'invited_by_email', 'created_at', 'expires_at']
        read_only_fields = ['id', 'token', 'status', 'created_at', 'expires_at', 'invited_by_email']
