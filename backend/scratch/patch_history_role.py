import re

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

history_block = """    @action(detail=True, methods=['get'], url_path='history')
    def history(self, request, pk=None):
        org = self.get_object()
        
        # 1. Fetch join requests
        join_reqs = OrganizationJoinRequest.objects.filter(organization=org).select_related('user').order_by('-requested_at')
        
        # 2. Fetch legacy invitations
        invites = OrganizationInvitation.objects.filter(organization=org).select_related('invited_by').order_by('-created_at')
        
        # 2b. Fetch new style invitations (members who were invited, regardless of acceptance)
        invitation_memberships = OrganizationMembership.objects.filter(organization=org, invited_by__isnull=False, is_active=True).select_related('user', 'invited_by').order_by('-joined_at')

        
        # 3. Fetch soft-deleted memberships (removed members)
        removed_members = OrganizationMembership.objects.filter(organization=org, is_active=False).select_related('user').order_by('-joined_at')
        
        # 4. Fetch soft-deleted notes
        from notes.models import Note
        deleted_notes = Note.objects.filter(organization=org, is_active=False).select_related('user').order_by('-updated_at')

        # 5. Fetch soft-deleted goals
        from goals.models import Goals
        deleted_goals = Goals.objects.filter(organization=org, is_deleted=True).select_related('created_by').order_by('-updated_at')"""

new_history_block = """    @action(detail=True, methods=['get'], url_path='history')
    def history(self, request, pk=None):
        org = self.get_object()
        
        try:
            membership = OrganizationMembership.objects.get(organization=org, user=request.user, is_active=True)
            is_owner_or_admin = membership.role in ['owner', 'admin']
        except OrganizationMembership.DoesNotExist:
            is_owner_or_admin = False
            
        # Base querysets
        join_reqs_qs = OrganizationJoinRequest.objects.filter(organization=org).select_related('user').order_by('-requested_at')
        invites_qs = OrganizationInvitation.objects.filter(organization=org).select_related('invited_by').order_by('-created_at')
        invitation_memberships_qs = OrganizationMembership.objects.filter(organization=org, invited_by__isnull=False, is_active=True).select_related('user', 'invited_by').order_by('-joined_at')
        removed_members_qs = OrganizationMembership.objects.filter(organization=org, is_active=False).select_related('user').order_by('-joined_at')
        
        from notes.models import Note
        deleted_notes_qs = Note.objects.filter(organization=org, is_active=False).select_related('user').order_by('-updated_at')
        
        from goals.models import Goals
        deleted_goals_qs = Goals.objects.filter(organization=org, is_deleted=True).select_related('created_by').order_by('-updated_at')
        
        # Filter based on role
        if not is_owner_or_admin:
            # Members only see their own activities
            join_reqs = join_reqs_qs.filter(user=request.user)
            invites = invites_qs.filter(invited_by=request.user)
            invitation_memberships = invitation_memberships_qs.filter(invited_by=request.user)
            removed_members = removed_members_qs.filter(user=request.user) # Probably shouldn't happen but safe
            deleted_notes = deleted_notes_qs.filter(user=request.user)
            deleted_goals = deleted_goals_qs.filter(created_by=request.user)
        else:
            join_reqs = join_reqs_qs
            invites = invites_qs
            invitation_memberships = invitation_memberships_qs
            removed_members = removed_members_qs
            deleted_notes = deleted_notes_qs
            deleted_goals = deleted_goals_qs"""

if "membership = OrganizationMembership.objects.get" not in content:
    content = content.replace(history_block, new_history_block)
    with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
print("organizations/views.py patched for role-based history")
