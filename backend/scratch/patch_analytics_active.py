import re

with open('c:/Users/saura/ParseOps/backend/analytics/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """        try:
            organization = Organization.objects.get(id=org_id)
            membership = OrganizationMembership.objects.get(organization=organization, user=request.user)
        except (Organization.DoesNotExist, OrganizationMembership.DoesNotExist):
            return Response({"error": "Organization not found or access denied."}, status=403)"""

replacement = """        try:
            organization = Organization.objects.get(id=org_id)
            membership = OrganizationMembership.objects.get(organization=organization, user=request.user, is_active=True)
        except (Organization.DoesNotExist, OrganizationMembership.DoesNotExist):
            return Response({"error": "Organization not found or access denied.", "detail": "You are not an active member of this organization."}, status=403)"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/backend/analytics/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("analytics/views.py patched to check is_active=True and return specific detail.")
