import re

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """            # Create membership
            OrganizationMembership.objects.get_or_create(
                organization=org,
                user=join_req.user,
                defaults={'role': join_req.requested_role}
            )"""

replacement = """            # Create or update membership
            membership, created = OrganizationMembership.objects.get_or_create(
                organization=org,
                user=join_req.user,
                defaults={'role': join_req.requested_role, 'is_active': True}
            )
            if not created and not membership.is_active:
                membership.is_active = True
                membership.role = join_req.requested_role
                membership.save()"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("manage_request patched to reactivate memberships")
