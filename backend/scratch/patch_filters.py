import re

with open('c:/Users/saura/ParseOps/backend/notifications/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

queryset_block = """    def get_queryset(self):
        # Return notifications belonging to the logged-in user, ordered by newest first
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')"""

new_queryset_block = """    def get_queryset(self):
        org_slug = self.request.query_params.get('org')
        member_id = self.request.query_params.get('member')
        
        qs = Notification.objects.all().order_by('-created_at')
        
        if org_slug:
            from organizations.models import OrganizationMembership, Organization
            org = Organization.objects.filter(name=org_slug).first()
            if not org:
                return Notification.objects.none()
                
            membership = OrganizationMembership.objects.filter(organization=org, user=self.request.user, is_active=True).first()
            if not membership:
                return Notification.objects.none()
                
            qs = qs.filter(organization=org)
            
            if membership.role in ['owner', 'admin']:
                if member_id:
                    qs = qs.filter(user_id=member_id)
            else:
                qs = qs.filter(user=self.request.user)
        else:
            qs = qs.filter(user=self.request.user)
            
        return qs"""

if "org_slug = self.request.query_params.get" not in content:
    content = content.replace(queryset_block, new_queryset_block)
    with open('c:/Users/saura/ParseOps/backend/notifications/views.py', 'w', encoding='utf-8') as f:
        f.write(content)

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'r', encoding='utf-8') as f:
    org_content = f.read()

history_block = """        # Filter based on role
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

new_history_block = """        # Filter based on role
        member_id = request.query_params.get('member')
        
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
                deleted_goals = deleted_goals_qs"""

if "member_id = request.query_params.get('member')" not in org_content:
    org_content = org_content.replace(history_block, new_history_block)
    
    # Also we should add Tasks and Extensions to the history log!
    # Tasks: created/updated. Wait, task creation is not tracked in a history log. 
    # But we can query Tasks and Extensions directly.
    task_import = """        from goals.models import Goals"""
    new_task_import = """        from tasks.models import Task, ExtensionRequest
        from goals.models import Goals"""
    org_content = org_content.replace(task_import, new_task_import)

    # Let's write the full updated history endpoint.
    
    with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'w', encoding='utf-8') as f:
        f.write(org_content)

print("Backend patched for member filters")
