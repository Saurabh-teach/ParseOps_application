import re

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

replacement = '''        # 2. Fetch legacy invitations
        invites = OrganizationInvitation.objects.filter(organization=org).select_related('invited_by').order_by('-created_at')
        
        # 2b. Fetch new style pending invitations (temp password users)
        pending_invites = OrganizationMembership.objects.filter(organization=org, user__must_change_password=True, is_active=True).select_related('user', 'invited_by')
'''
content = content.replace("        # 2. Fetch invitations\n        invites = OrganizationInvitation.objects.filter(organization=org).select_related('invited_by').order_by('-created_at')", replacement)

loop_replacement = '''        for i in invites:
            history_data.append({
                "id": str(i.id),
                "type": "invitation",
                "email": i.email,
                "role": i.role,
                "invited_by": i.invited_by.email if i.invited_by else "System",
                "status": i.status,
                "timestamp": i.created_at
            })
            
        for p in pending_invites:
            history_data.append({
                "id": str(p.id),
                "type": "invitation",
                "email": p.user.email,
                "role": p.role,
                "invited_by": p.invited_by.email if p.invited_by else "System",
                "status": "pending",
                "timestamp": p.joined_at
            })'''
content = content.replace('''        for i in invites:
            history_data.append({
                "id": str(i.id),
                "type": "invitation",
                "email": i.email,
                "role": i.role,
                "invited_by": i.invited_by.email if i.invited_by else "System",
                "status": i.status,
                "timestamp": i.created_at
            })''', loop_replacement)

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
