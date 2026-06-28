import re

with open('c:/Users/saura/ParseOps/backend/organizations/serializers.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """        if OrganizationMembership.objects.filter(organization=org, user=user).exists():
            raise serializers.ValidationError("You are already a member of this workspace.")"""

replacement = """        if OrganizationMembership.objects.filter(organization=org, user=user, is_active=True).exists():
            raise serializers.ValidationError("You are already a member of this workspace.")"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/backend/organizations/serializers.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("JoinRequestSerializer patched to allow join requests from inactive members")
