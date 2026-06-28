from django.db import transaction
from rest_framework import status, permissions, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from .models import Organization, OrganizationMembership, OrganizationJoinRequest, OrganizationInvitation
from .serializers import OrganizationSerializer, JoinRequestSerializer, InvitationSerializer
from .permissions import IsOrganizationOwner, IsOrganizationAdmin, IsOrganizationMember
from django.contrib.auth import get_user_model

User = get_user_model()

class OrganizationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationSerializer
    queryset = Organization.objects.all()

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['destroy', 'deactivate', 'reactivate']:
            permission_classes = [permissions.IsAuthenticated, IsOrganizationOwner]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [permissions.IsAuthenticated, IsOrganizationAdmin]
        elif self.action in ['invite', 'manage_request', 'remove_member', 'change_role', 'restore_member', 'pending_invitations', 'cancel_invitation']:
            permission_classes = [permissions.IsAuthenticated, IsOrganizationAdmin]
        elif self.action in ['members', 'member_detail', 'retrieve', 'list_join_requests']:
            permission_classes = [permissions.IsAuthenticated, IsOrganizationMember]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        # Return active public orgs OR orgs where user is an active member OR orgs where user has a pending invitation
        # AND return inactive/deactivated orgs where the user is the owner (so they can restore it)
        return Organization.objects.filter(
            Q(is_active=True) & (
                Q(is_public=True) | 
                Q(memberships__user=self.request.user, memberships__is_active=True) |
                Q(invitations__email__iexact=self.request.user.email, invitations__status='pending')
            ) |
            Q(is_active=False) & Q(owner=self.request.user)
        ).distinct().annotate(
            member_count=Count('memberships', filter=Q(memberships__is_active=True))
        )

    @transaction.atomic
    def perform_create(self, serializer):
        # When an organization is created, the creator becomes the OWNER automatically
        org = serializer.save(created_by=self.request.user, owner=self.request.user)
        OrganizationMembership.objects.create(
            organization=org,
            user=self.request.user,
            role='owner'
        )

    def destroy(self, request, *args, **kwargs):
        # Permanent delete
        org = self.get_object()
        org.delete()
        return Response({"message": "Workspace permanently deleted successfully!"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate(self, request, pk=None):
        # Soft delete / deactivation
        org = self.get_object()
        org.is_active = False
        org.save()
        return Response({"message": "Workspace deactivated successfully!"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='reactivate')
    def reactivate(self, request, pk=None):
        # Reactivate workspace
        org = self.get_object()
        org.is_active = True
        org.save()
        return Response({"message": "Workspace reactivated successfully!"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='join-request')
    def join_request(self, request, pk=None):
        org = self.get_object()
        
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        msg = data.get('message')
        if not msg or not str(msg).strip():
            data['message'] = f"I would like to join your workspace '{org.name}' to collaborate with the team."
        else:
            data['message'] = str(msg).strip()
            
        # Check for existing pending join request
        existing_request = OrganizationJoinRequest.objects.filter(organization=org, user=request.user, status='pending').first()
        if existing_request:
            return Response({"error": "Join request already pending for this organization."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = JoinRequestSerializer(data={'organization': org.id, **data}, context={'request': request})
        
        if serializer.is_valid():
            join_req = serializer.save(user=request.user)
            try:
                from notifications.organization import create_join_request_notification
                create_join_request_notification(join_req)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error creating join request notification: {e}")
            return Response({"message": "Join request submitted successfully!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='invite')
    @transaction.atomic
    def invite(self, request, pk=None):
        org = self.get_object()
        email = request.data.get('email')
        role = request.data.get('role', 'member')
        message = request.data.get('message')
        
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        import string, secrets, uuid
        from django.contrib.auth import get_user_model
        from organizations.models import OrganizationMembership, OrganizationInvitation
        from django.utils import timezone
        from datetime import timedelta
        
        User = get_user_model()
        user = User.objects.filter(email__iexact=email).first()
        temp_password = None
        
        # Check if already an active member in org
        if user:
            existing = OrganizationMembership.objects.filter(organization=org, user=user, is_active=True).first()
            if existing:
                return Response({"error": "User is already a member of this organization."}, status=status.HTTP_400_BAD_REQUEST)
            
        if not user:
            # Generate secure temporary password
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
            # Ensure at least one of each to meet strong password requirements
            temp_password = (
                secrets.choice(string.ascii_lowercase) +
                secrets.choice(string.ascii_uppercase) +
                secrets.choice(string.digits) +
                secrets.choice("!@#$%^&*") +
                ''.join(secrets.choice(alphabet) for i in range(8))
            )
            # Shuffle the password so the predictable characters aren't always at the beginning
            temp_password_list = list(temp_password)
            secrets.SystemRandom().shuffle(temp_password_list)
            temp_password = ''.join(temp_password_list)
            
            user = User.objects.create_user(
                email=email,
                password=temp_password
            )
            user.must_change_password = True
            user.save()

        # Check for existing pending invitation
        existing_invite = OrganizationInvitation.objects.filter(organization=org, email__iexact=email, status='pending').first()
        if existing_invite:
            return Response({"error": "Invitation already sent to this email and is pending."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Generate secure unique invitation token
        token = uuid.uuid4().hex
        
        invitation = OrganizationInvitation.objects.create(
            organization=org,
            email=email,
            role=role,
            token=token,
            status='pending',
            message=message,
            invited_by=request.user,
            expires_at=timezone.now() + timedelta(days=7)
        )
            
        try:
            from notifications.organization import create_invitation_notification
            create_invitation_notification(invitation, temp_password=temp_password)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error creating invitation notification: {e}")
            
        return Response({
            "message": f"Invitation sent to {email}"
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='pending-invitations')
    def pending_invitations(self, request, pk=None):
        org = self.get_object()
        invitations = OrganizationInvitation.objects.filter(organization=org, status='pending')
        serializer = InvitationSerializer(invitations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='cancel-invitation')
    def cancel_invitation(self, request, pk=None):
        org = self.get_object()
        invitation_id = request.data.get('invitation_id')
        if not invitation_id:
            return Response({"error": "Invitation ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            invitation = OrganizationInvitation.objects.get(id=invitation_id, organization=org, status='pending')
        except OrganizationInvitation.DoesNotExist:
            return Response({"error": "Pending invitation not found."}, status=status.HTTP_404_NOT_FOUND)
        
        email = invitation.email
        invitation.status = 'cancelled'
        invitation.save()
        
        # If the user was created just for this invite (never logged in, no other invites/memberships), delete them
        # so that a future invite will re-trigger the "new user" flow with a temporary password.
        from django.contrib.auth import get_user_model
        from organizations.models import OrganizationMembership
        User = get_user_model()
        user = User.objects.filter(email__iexact=email).first()
        
        if user and user.last_login is None:
            has_other_invites = OrganizationInvitation.objects.filter(email__iexact=email, status='pending').exclude(id=invitation_id).exists()
            has_memberships = OrganizationMembership.objects.filter(user=user).exists()
            if not has_other_invites and not has_memberships:
                user.delete()
                
        return Response({"message": "Invitation cancelled successfully!"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='members')
    def members(self, request, pk=None):
        org = self.get_object()
        memberships = OrganizationMembership.objects.filter(
            organization=org, 
            is_active=True
        ).select_related('user')
        from .serializers import MemberDetailSerializer
        serializer = MemberDetailSerializer(memberships, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='members/(?P<member_id>[^/.]+)')
    def member_detail(self, request, pk=None, member_id=None):
        org = self.get_object()
        try:
            membership = OrganizationMembership.objects.get(id=member_id, organization=org)
        except OrganizationMembership.DoesNotExist:
            return Response({"error": "Member not found in organization."}, status=status.HTTP_404_NOT_FOUND)
        
        from .serializers import MemberDetailSerializer
        serializer = MemberDetailSerializer(membership)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='remove-member')
    def remove_member(self, request, pk=None):
        org = self.get_object()
        member_id = request.data.get('member_id') # membership ID
        
        if not member_id:
            return Response({"error": "Member ID is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            membership = OrganizationMembership.objects.get(id=member_id, organization=org)
        except OrganizationMembership.DoesNotExist:
            return Response({"error": "Member not found in organization."}, status=status.HTTP_404_NOT_FOUND)
            
        # Owner cannot be removed via simple delete, unless ownership is transferred first
        if membership.role == 'owner':
            return Response({"error": "Cannot remove the owner of the organization. Transfer ownership first."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Admins cannot remove other admins if they are not the owner
        requesting_membership = OrganizationMembership.objects.get(organization=org, user=request.user)
        if membership.role == 'admin' and requesting_membership.role != 'owner':
            return Response({"error": "Only the owner can remove administrators."}, status=status.HTTP_403_FORBIDDEN)
            
        user_email = membership.user.email
        
        # Soft delete membership so it STILL SHOWS UP in the Workspace History logs
        membership.is_active = False
        membership.save()
        
        # As requested: he only login in there login password connot access workspace okay
        # We do NOT disable user.is_active, so they can still log in but will see no workspace.
        user = membership.user
        
        # Add to python logs
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"User {user_email} removed from org {org.name}. Logged in Workspace History.")
        
        # Send WebSocket signal to kick the user
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"chat_user_{org.id}_{membership.user.id}",
                {
                    'type': 'workspace_access_lost',
                    'org_id': str(org.id)
                }
            )
            
        return Response({"message": "Member removed successfully!"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='restore-member')
    def restore_member(self, request, pk=None):
        org = self.get_object()
        member_id = request.data.get('member_id')
        
        if not member_id:
            return Response({"error": "Member ID is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            membership = OrganizationMembership.objects.get(id=member_id, organization=org)
        except OrganizationMembership.DoesNotExist:
            return Response({"error": "Member not found in organization."}, status=status.HTTP_404_NOT_FOUND)
            
        membership.is_active = True
        membership.save()
        return Response({"message": "Member restored successfully!"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='change-role')
    def change_role(self, request, pk=None):
        org = self.get_object()
        member_id = request.data.get('member_id') # membership ID
        new_role = request.data.get('role')
        
        if not member_id or not new_role:
            return Response({"error": "Member ID and role are required."}, status=status.HTTP_400_BAD_REQUEST)
            
        if new_role not in ['admin', 'member', 'owner']:
            return Response({"error": "Invalid role specified."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            membership = OrganizationMembership.objects.get(id=member_id, organization=org)
        except OrganizationMembership.DoesNotExist:
            return Response({"error": "Member not found in organization."}, status=status.HTTP_404_NOT_FOUND)
            
        requesting_membership = OrganizationMembership.objects.get(organization=org, user=request.user)
        
        from django.core.exceptions import ValidationError
        
        if requesting_membership.role != 'owner':
            return Response({"error": "Only an organization owner can change roles."}, status=status.HTTP_403_FORBIDDEN)
            
        if new_role == 'owner':
            membership.role = 'owner'
            membership.save()
            # If org.owner is somehow tied, let's keep it sync with the first owner or do nothing.
            # We don't strictly need org.owner if we use OrganizationMembership for everything.
            return Response({"message": "Member promoted to owner successfully!"}, status=status.HTTP_200_OK)
            
        if membership.role == 'owner' and new_role != 'owner':
            if membership.user == request.user:
                return Response({"error": "You cannot demote yourself. Another owner must demote you."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                membership.role = new_role
                membership.save()
                return Response({"message": f"Owner demoted to {new_role} successfully!"}, status=status.HTTP_200_OK)
            except ValidationError as e:
                return Response({"error": str(e.messages[0]) if hasattr(e, 'messages') else str(e)}, status=status.HTTP_400_BAD_REQUEST)
                
        membership.role = new_role
        membership.save()
        return Response({"message": f"Member role updated to {new_role} successfully!"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='change-permissions')
    def change_permissions(self, request, pk=None):
        org = self.get_object()
        member_id = request.data.get('member_id')
        custom_perms = request.data.get('custom_permissions')
        
        if not member_id:
            return Response({"error": "Member ID is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            membership = OrganizationMembership.objects.get(id=member_id, organization=org)
        except OrganizationMembership.DoesNotExist:
            return Response({"error": "Member not found in organization."}, status=status.HTTP_404_NOT_FOUND)
            
        requesting_membership = OrganizationMembership.objects.get(organization=org, user=request.user)
        
        # HIERARCHY RULES:
        # 1. Non-admins/non-owners cannot modify permissions
        if requesting_membership.role not in ['owner', 'admin']:
            return Response({"error": "Only owners and administrators can manage permissions."}, status=status.HTTP_403_FORBIDDEN)
            
        # 2. Cannot modify the owner's permissions
        if membership.role == 'owner':
            return Response({"error": "Cannot modify permissions for the organization owner."}, status=status.HTTP_403_FORBIDDEN)
            
        # 3. Admins cannot modify permissions of other admins or owners
        if requesting_membership.role == 'admin' and membership.role == 'admin':
            return Response({"error": "Administrators cannot modify permissions of other administrators."}, status=status.HTTP_403_FORBIDDEN)
            
        # Update permissions
        membership.custom_permissions = custom_perms
        membership.save()
        
        return Response({
            "message": "Permissions updated successfully!",
            "custom_permissions": membership.custom_permissions
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='calendar-events')
    def calendar_events(self, request, pk=None):
        org = self.get_object()
        membership = get_object_or_404(OrganizationMembership, organization=org, user=request.user, is_active=True)
        is_manager = membership.role in ['admin', 'owner']

        start_date = request.query_params.get('start')
        end_date = request.query_params.get('end')

        from tasks.models import Task
        from goals.models import Goals
        from django.db.models import Q
        import datetime

        # Tasks Query
        task_query = Q(organization=org, is_deleted=False)
        if not is_manager:
            task_query &= Q(assignee=request.user)

        if start_date and end_date:
            try:
                s_dt = datetime.datetime.strptime(start_date[:10], '%Y-%m-%d')
                e_dt = datetime.datetime.strptime(end_date[:10], '%Y-%m-%d')
                task_query &= (Q(due_date__gte=s_dt) | Q(start_date__lte=e_dt))
            except ValueError:
                pass

        tasks = Task.objects.filter(task_query).select_related('assignee').distinct()

        # Goals Query
        goal_query = Q(organization=org)
        if not is_manager:
            goal_query &= (Q(owner=request.user) | Q(assignees=request.user))

        if start_date and end_date:
            try:
                s_dt = datetime.datetime.strptime(start_date[:10], '%Y-%m-%d').date()
                e_dt = datetime.datetime.strptime(end_date[:10], '%Y-%m-%d').date()
                goal_query &= (Q(due_date__gte=s_dt) | Q(start_date__lte=e_dt))
            except ValueError:
                pass

        goals = Goals.objects.filter(goal_query).distinct()

        events = []
        for t in tasks:
            start = t.start_date.isoformat() if t.start_date else (t.created_at.date().isoformat() if t.created_at else None)
            end = t.due_date.isoformat() if t.due_date else start
            color = '#fef08a' if t.priority == 'urgent' else ('#fecaca' if t.priority == 'high' else ('#bfdbfe' if t.priority == 'medium' else '#d9f99d'))
            events.append({
                'id': f"task_{t.id}",
                'title': f"[Task] {t.title}",
                'start': start,
                'end': end,
                'allDay': False if t.due_date and t.due_date.hour > 0 else True,
                'backgroundColor': color,
                'borderColor': color,
                'textColor': '#0f172a',
                'extendedProps': {
                    'type': 'task',
                    'original_id': str(t.id),
                    'status': t.status,
                    'priority': t.priority,
                    'estimated_hours': float(t.estimated_hours) if t.estimated_hours else (t.estimated_minutes/60.0 if t.estimated_minutes else 0),
                    'assignee_id': str(t.assignee.id) if t.assignee else None,
                    'assignee_name': (t.assignee.first_name + ' ' + t.assignee.last_name).strip() if t.assignee and (t.assignee.first_name or t.assignee.last_name) else (t.assignee.email if t.assignee else 'Unassigned'),
                    'assignee_email': t.assignee.email if t.assignee else None,
                }
            })

        for g in goals:
            start = g.start_date.isoformat() if g.start_date else None
            end = g.due_date.isoformat() if g.due_date else start
            events.append({
                'id': f"goal_{g.id}",
                'title': f"[Goal] {g.title}",
                'start': start,
                'end': end,
                'allDay': True,
                'backgroundColor': '#c084fc',
                'borderColor': '#a855f7',
                'textColor': '#ffffff',
                'extendedProps': {
                    'type': 'goal',
                    'original_id': str(g.id),
                    'status': g.status,
                    'progress': g.progress
                }
            })

        # Leaves Query
        from users.models import LeaveRequest
        leave_query = Q(status='Approved', organization=org)
        if not is_manager:
            leave_query &= Q(user=request.user)

        if start_date and end_date:
            try:
                s_dt = datetime.datetime.strptime(start_date[:10], '%Y-%m-%d').date()
                e_dt = datetime.datetime.strptime(end_date[:10], '%Y-%m-%d').date()
                leave_query &= (Q(end_date__gte=s_dt) & Q(start_date__lte=e_dt))
            except ValueError:
                pass

        leaves = LeaveRequest.objects.filter(leave_query).select_related('user')
        for lv in leaves:
            events.append({
                'id': f"leave_{lv.id}",
                'title': f"[On Leave] {lv.user.first_name} {lv.user.last_name}".strip() or lv.user.email,
                'start': lv.start_date.isoformat(),
                'end': lv.end_date.isoformat(),
                'allDay': True,
                'backgroundColor': '#f87171',
                'borderColor': '#ef4444',
                'textColor': '#ffffff',
                'extendedProps': {
                    'type': 'leave',
                    'original_id': str(lv.id),
                    'user': lv.user.email,
                    'leave_type': lv.leave_type,
                    'reason': lv.reason
                }
            })

        return Response(events)

    @action(detail=False, methods=['get'], url_path='my-workspaces')
    def my_workspaces(self, request):
        # Returns workspaces where the user is an active member
        orgs = Organization.objects.filter(
            memberships__user=request.user, 
            is_active=True
        ).distinct().annotate(
            member_count=Count('memberships', filter=Q(memberships__is_active=True))
        )
        serializer = self.get_serializer(orgs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='join-requests')
    def list_join_requests(self, request, pk=None):
        org = self.get_object()
        requests = OrganizationJoinRequest.objects.filter(organization=org, status='pending').select_related('user')
        data = []
        for r in requests:
            data.append({
                "id": r.id,
                "email": r.user.email,
                "first_name": getattr(r.user, 'first_name', ''),
                "last_name": getattr(r.user, 'last_name', ''),
                "job_title": getattr(r.user, 'job_title', ''),
                "department": getattr(r.user, 'department', ''),
                "education": getattr(r.user, 'education', ''),
                "bio": getattr(r.user, 'bio', ''),
                "requested_role": r.requested_role,
                "message": r.message,
                "created_at": r.requested_at
            })
        return Response(data)

    @action(detail=True, methods=['get'], url_path='history')
    def history(self, request, pk=None):
        org = self.get_object()
        
        try:
            membership = OrganizationMembership.objects.get(organization=org, user=request.user, is_active=True)
            is_owner_or_admin = membership.role in ['owner', 'admin']
        except OrganizationMembership.DoesNotExist:
            is_owner_or_admin = False
            
        member_id = request.query_params.get('member')
        
        # Base querysets
        join_reqs_qs = OrganizationJoinRequest.objects.filter(organization=org).select_related('user').order_by('-requested_at')
        invites_qs = OrganizationInvitation.objects.filter(organization=org).select_related('invited_by').order_by('-created_at')
        invitation_memberships_qs = OrganizationMembership.objects.filter(organization=org, invited_by__isnull=False, is_active=True).select_related('user', 'invited_by').order_by('-joined_at')
        removed_members_qs = OrganizationMembership.objects.filter(organization=org, is_active=False).select_related('user').order_by('-joined_at')
        
        from notes.models import Note
        deleted_notes_qs = Note.objects.filter(organization=org, is_active=False).select_related('user').order_by('-updated_at')
        
        from goals.models import Goals
        deleted_goals_qs = Goals.objects.filter(organization=org, is_deleted=True).select_related('created_by').order_by('-updated_at')
        
        if not is_owner_or_admin:
            # Members only see their own activities
            join_reqs = join_reqs_qs.filter(user=request.user)
            invites = invites_qs.filter(invited_by=request.user)
            invitation_memberships = invitation_memberships_qs.filter(invited_by=request.user)
            removed_members = removed_members_qs.filter(user=request.user)
            deleted_notes = deleted_notes_qs.filter(user=request.user)
            deleted_goals = deleted_goals_qs.filter(created_by=request.user)
        else:
            if member_id:
                # Owner filtering by specific member
                join_reqs = join_reqs_qs.filter(user_id=member_id)
                invites = invites_qs.filter(invited_by_id=member_id)
                invitation_memberships = invitation_memberships_qs.filter(invited_by_id=member_id)
                removed_members = removed_members_qs.filter(user_id=member_id)
                deleted_notes = deleted_notes_qs.filter(user_id=member_id)
                deleted_goals = deleted_goals_qs.filter(created_by_id=member_id)
            else:
                join_reqs = join_reqs_qs
                invites = invites_qs
                invitation_memberships = invitation_memberships_qs
                removed_members = removed_members_qs
                deleted_notes = deleted_notes_qs
                deleted_goals = deleted_goals_qs
        
        history_data = []
        
        for r in join_reqs:
            history_data.append({
                "id": str(r.id),
                "type": "join_request",
                "email": r.user.email,
                "role": r.requested_role,
                "message": r.message,
                "status": r.status,
                "timestamp": r.requested_at
            })
            
        for i in invites:
            history_data.append({
                "id": str(i.id),
                "type": "invitation",
                "email": i.email,
                "role": i.role,
                "invited_by": i.invited_by.email if i.invited_by else "System",
                "status": i.status,
                "timestamp": i.created_at
            })
            
        for p in invitation_memberships:
            history_data.append({
                "id": str(p.id),
                "type": "invitation",
                "email": p.user.email,
                "role": p.role,
                "invited_by": p.invited_by.email if p.invited_by else "System",
                "status": "pending" if p.user.must_change_password else "accepted",
                "timestamp": p.joined_at
            })
            
        for m in removed_members:
            history_data.append({
                "id": str(m.id),
                "type": "removed_member",
                "email": m.user.email,
                "role": m.role,
                "timestamp": m.joined_at 
            })
            
        for n in deleted_notes:
            history_data.append({
                "id": str(n.id),
                "type": "deleted_note",
                "title": n.title,
                "user": n.user.email,
                "timestamp": n.updated_at
            })

        for g in deleted_goals:
            history_data.append({
                "id": str(g.id),
                "type": "deleted_goal",
                "title": g.title,
                "user": g.created_by.email if g.created_by else "System",
                "timestamp": g.updated_at
            })
            
        history_data.sort(key=lambda x: x['timestamp'], reverse=True)
        return Response(history_data)

    @action(detail=True, methods=['post'], url_path='manage-request')
    def manage_request(self, request, pk=None):
        org = self.get_object()
        request_id = request.data.get('request_id')
        action = request.data.get('action') # 'approve' or 'deny'
        
        try:
            join_req = OrganizationJoinRequest.objects.get(id=request_id, organization=org)
        except OrganizationJoinRequest.DoesNotExist:
            return Response({"error": "Request not found"}, status=status.HTTP_404_NOT_FOUND)
            
        if action == 'approve':
            from django.utils import timezone
            join_req.status = 'approved'
            join_req.reviewed_by = request.user
            join_req.reviewed_at = timezone.now()
            join_req.save()
            # Create or update membership
            membership, created = OrganizationMembership.objects.get_or_create(
                organization=org,
                user=join_req.user,
                defaults={'role': join_req.requested_role, 'is_active': True}
            )
            if not created and not membership.is_active:
                membership.is_active = True
                membership.role = join_req.requested_role
                membership.save()
            try:
                from notifications.organization import create_join_request_reviewed_notification
                create_join_request_reviewed_notification(join_req)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error creating join request approved notification: {e}")
            return Response({"message": "Request approved!"})
        elif action == 'deny':
            from django.utils import timezone
            join_req.status = 'denied'
            join_req.reviewed_by = request.user
            join_req.reviewed_at = timezone.now()
            join_req.save()
            try:
                from notifications.organization import create_join_request_reviewed_notification
                create_join_request_reviewed_notification(join_req)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error creating join request denied notification: {e}")
            return Response({"message": "Request denied!"})
        else:
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='accept-invitation')
    def accept_invitation(self, request):
        invitation_id = request.data.get('invitation_id')
        token = request.data.get('token')
        
        if not invitation_id and not token:
            return Response({"error": "Either invitation_id or token is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            if invitation_id:
                import uuid
                is_uuid = False
                try:
                    uuid.UUID(str(invitation_id))
                    is_uuid = True
                except ValueError:
                    pass
                
                if is_uuid:
                    invitation = OrganizationInvitation.objects.get(id=invitation_id)
                else:
                    invitation = OrganizationInvitation.objects.get(token=invitation_id)
            else:
                invitation = OrganizationInvitation.objects.get(token=token)
        except (OrganizationInvitation.DoesNotExist, ValueError):
            return Response({"error": "Invitation not found."}, status=status.HTTP_404_NOT_FOUND)
            
        # Verify invitation status
        if invitation.status != 'pending':
            return Response({"error": f"Invitation is already {invitation.status}."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Verify expiration
        from django.utils import timezone
        if invitation.expires_at < timezone.now():
            invitation.status = 'expired'
            invitation.save()
            return Response({"error": "Invitation has expired."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Verify email matches logged-in user
        if invitation.email.lower() != request.user.email.lower():
            return Response({"error": "This invitation was sent to a different email address."}, status=status.HTTP_403_FORBIDDEN)
            
        # Add member
        membership, created = OrganizationMembership.objects.get_or_create(
            organization=invitation.organization,
            user=request.user,
            defaults={'role': invitation.role, 'is_active': True}
        )
        
        if not created:
            # User is already a member, upgrade role if specified
            membership.role = invitation.role
            membership.is_active = True
            membership.save()
            
        invitation.status = 'accepted'
        invitation.save()
        
        try:
            from notifications.organization import create_invitation_accepted_notification
            create_invitation_accepted_notification(invitation)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error creating invitation accepted notification: {e}")
        
        # Mark invitation notification as read for this user if it exists
        from notifications.models import Notification
        Notification.objects.filter(
            user=request.user, 
            notification_type='invitation', 
            data__invitation_id=str(invitation.id)
        ).update(is_read=True)
        
        return Response({
            "message": "Invitation accepted successfully!",
            "organization": {
                "id": str(invitation.organization.id),
                "name": invitation.organization.name
            }
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='decline-invitation')
    def decline_invitation(self, request):
        invitation_id = request.data.get('invitation_id')
        token = request.data.get('token')
        
        if not invitation_id and not token:
            return Response({"error": "Either invitation_id or token is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            if invitation_id:
                invitation = OrganizationInvitation.objects.get(id=invitation_id)
            else:
                invitation = OrganizationInvitation.objects.get(token=token)
        except (OrganizationInvitation.DoesNotExist, ValueError):
            return Response({"error": "Invitation not found."}, status=status.HTTP_404_NOT_FOUND)
            
        if invitation.status != 'pending':
            return Response({"error": f"Invitation is already {invitation.status}."}, status=status.HTTP_400_BAD_REQUEST)
            
        if invitation.email.lower() != request.user.email.lower():
            return Response({"error": "This invitation was sent to a different email address."}, status=status.HTTP_403_FORBIDDEN)
            
        invitation.status = 'expired'
        invitation.save()
        
        try:
            from notifications.organization import create_invitation_declined_notification
            create_invitation_declined_notification(invitation)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error creating invitation declined notification: {e}")
        
        # Mark invitation notification as read
        from notifications.models import Notification
        Notification.objects.filter(
            user=request.user, 
            notification_type='invitation', 
            data__invitation_id=str(invitation.id)
        ).update(is_read=True)
        
        return Response({"message": "Invitation declined successfully!"}, status=status.HTTP_200_OK)
