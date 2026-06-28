import re

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """        # Check if already in org
        if OrganizationMembership.objects.filter(organization=org, user=user).exists():
            return Response({"error": "User is already a member of this organization."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Add to org immediately
        OrganizationMembership.objects.create(
            organization=org,
            user=user,
            role=role,
            invited_by=request.user
        )"""

replacement = """        # Check if already in org
        existing = OrganizationMembership.objects.filter(organization=org, user=user).first()
        if existing:
            if existing.is_active:
                return Response({"error": "User is already a member of this organization."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Reactivate previously removed member
                existing.is_active = True
                existing.role = role
                existing.invited_by = request.user
                existing.save()
        else:
            # Add to org immediately
            OrganizationMembership.objects.create(
                organization=org,
                user=user,
                role=role,
                invited_by=request.user
            )"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("organizations/views.py patched to reactivate soft-deleted members")
