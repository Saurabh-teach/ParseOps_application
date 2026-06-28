import re

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

start_idx = content.find("    @action(detail=True, methods=['get'], url_path='history')")
end_idx = content.find("    @action(detail=True, methods=['post'], url_path='manage-request')", start_idx)

if start_idx != -1 and end_idx != -1:
    new_history = """    @action(detail=True, methods=['get'], url_path='history')
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
        goals_qs = Goals.objects.filter(organization=org).select_related('created_by').order_by('-updated_at')
        deleted_goals_qs = goals_qs.filter(is_deleted=True)
        active_goals_qs = goals_qs.filter(is_deleted=False)
        
        from tasks.models import Task, ExtensionRequest
        tasks_qs = Task.objects.filter(goal__organization=org).select_related('assigned_to', 'goal').order_by('-updated_at')
        extensions_qs = ExtensionRequest.objects.filter(task__goal__organization=org).select_related('task__assigned_to').order_by('-created_at')
        
        if not is_owner_or_admin:
            # Members only see their own activities
            join_reqs = join_reqs_qs.filter(user=request.user)
            invites = invites_qs.filter(invited_by=request.user)
            invitation_memberships = invitation_memberships_qs.filter(invited_by=request.user)
            removed_members = removed_members_qs.filter(user=request.user)
            deleted_notes = deleted_notes_qs.filter(user=request.user)
            deleted_goals = deleted_goals_qs.filter(created_by=request.user)
            active_goals = active_goals_qs.filter(created_by=request.user)
            tasks = tasks_qs.filter(assigned_to=request.user)
            extensions = extensions_qs.filter(task__assigned_to=request.user)
        else:
            if member_id:
                # Owner filtering by specific member
                join_reqs = join_reqs_qs.filter(user_id=member_id)
                invites = invites_qs.filter(invited_by_id=member_id)
                invitation_memberships = invitation_memberships_qs.filter(invited_by_id=member_id)
                removed_members = removed_members_qs.filter(user_id=member_id)
                deleted_notes = deleted_notes_qs.filter(user_id=member_id)
                deleted_goals = deleted_goals_qs.filter(created_by_id=member_id)
                active_goals = active_goals_qs.filter(created_by_id=member_id)
                tasks = tasks_qs.filter(assigned_to_id=member_id)
                extensions = extensions_qs.filter(task__assigned_to_id=member_id)
            else:
                join_reqs = join_reqs_qs
                invites = invites_qs
                invitation_memberships = invitation_memberships_qs
                removed_members = removed_members_qs
                deleted_notes = deleted_notes_qs
                deleted_goals = deleted_goals_qs
                active_goals = active_goals_qs
                tasks = tasks_qs
                extensions = extensions_qs
        
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

        for g in active_goals:
            history_data.append({
                "id": str(g.id),
                "type": "goal_created",
                "title": g.title,
                "user": g.created_by.email if g.created_by else "System",
                "status": g.status,
                "timestamp": g.created_at
            })

        for t in tasks:
            history_data.append({
                "id": str(t.id),
                "type": "task_activity",
                "title": t.title,
                "user": t.assigned_to.email if t.assigned_to else "System",
                "status": t.status,
                "timestamp": t.updated_at
            })

        for e in extensions:
            history_data.append({
                "id": str(e.id),
                "type": "extension_request",
                "title": e.task.title,
                "user": e.task.assigned_to.email if e.task.assigned_to else "System",
                "status": e.status,
                "timestamp": e.created_at
            })
            
        history_data.sort(key=lambda x: x['timestamp'], reverse=True)
        return Response(history_data)

"""
    content = content[:start_idx] + new_history + content[end_idx:]
    with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("History logic fully updated")
else:
    print("Could not find history boundaries")
