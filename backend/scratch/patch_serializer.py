import re

with open('c:/Users/saura/ParseOps/backend/organizations/serializers.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """        # Check membership
        membership = OrganizationMembership.objects.filter(organization=obj, user=user).first()
        if membership:
            return {
                'type': 'member', 
                'role': membership.role,
                'custom_permissions': membership.custom_permissions or {}
            }"""

replacement = """        # Check membership
        membership = OrganizationMembership.objects.filter(organization=obj, user=user, is_active=True).first()
        if membership:
            return {
                'type': 'member', 
                'role': membership.role,
                'custom_permissions': membership.custom_permissions or {}
            }"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/backend/organizations/serializers.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("serializers.py patched for is_active=True in get_my_status")
