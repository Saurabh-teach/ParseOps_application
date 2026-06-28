import re

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the query
old_query = """        # 2b. Fetch new style pending invitations (temp password users)
        pending_invites = OrganizationMembership.objects.filter(organization=org, user__must_change_password=True, is_active=True).select_related('user', 'invited_by')"""

new_query = """        # 2b. Fetch new style invitations (members who were invited, regardless of acceptance)
        invitation_memberships = OrganizationMembership.objects.filter(organization=org, invited_by__isnull=False, is_active=True).select_related('user', 'invited_by').order_by('-joined_at')"""

content = content.replace(old_query, new_query)

# Replace the loop
old_loop = """        for p in pending_invites:
            history_data.append({
                "id": str(p.id),
                "type": "invitation",
                "email": p.user.email,
                "role": p.role,
                "invited_by": p.invited_by.email if p.invited_by else "System",
                "status": "pending",
                "timestamp": p.joined_at
            })"""

new_loop = """        for p in invitation_memberships:
            history_data.append({
                "id": str(p.id),
                "type": "invitation",
                "email": p.user.email,
                "role": p.role,
                "invited_by": p.invited_by.email if p.invited_by else "System",
                "status": "pending" if p.user.must_change_password else "accepted",
                "timestamp": p.joined_at
            })"""

content = content.replace(old_loop, new_loop)

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
