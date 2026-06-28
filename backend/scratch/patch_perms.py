import re

with open('c:/Users/saura/ParseOps/backend/core/permissions.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add import if missing
if 'from rest_framework.exceptions import PermissionDenied' not in content:
    content = "from rest_framework.exceptions import PermissionDenied\n" + content

def replace_membership_check(text):
    # Find patterns like:
    # if not membership: return False
    # and replace with:
    # if not membership: raise PermissionDenied("You are not an active member of this organization.")
    
    # Also patterns like:
    # return membership is not None and membership.role == 'owner'
    
    # For IsOrganizationOwner, IsOrganizationAdmin, IsOrganizationMember
    
    return text

# We will just manually replace the relevant parts for the specific classes

# IsOrganizationOwner
target_owner = """class IsOrganizationOwner(permissions.BasePermission):
    \"\"\"Full permissions - only accessible to organization Owners.\"\"\"
    def has_permission(self, request, view):
        org_id = extract_org_id(request, view)
        membership = get_member_membership(request, org_id)
        return membership is not None and membership.role == 'owner'

    def has_object_permission(self, request, view, obj):
        org_id = extract_org_id(request, view, obj)
        membership = get_member_membership(request, org_id)
        return membership is not None and membership.role == 'owner'"""

replacement_owner = """class IsOrganizationOwner(permissions.BasePermission):
    \"\"\"Full permissions - only accessible to organization Owners.\"\"\"
    def has_permission(self, request, view):
        org_id = extract_org_id(request, view)
        membership = get_member_membership(request, org_id)
        if not membership: raise PermissionDenied("You are not an active member of this organization.")
        return membership.role == 'owner'

    def has_object_permission(self, request, view, obj):
        org_id = extract_org_id(request, view, obj)
        membership = get_member_membership(request, org_id)
        if not membership: raise PermissionDenied("You are not an active member of this organization.")
        return membership.role == 'owner'"""

content = content.replace(target_owner, replacement_owner)


# IsOrganizationAdmin
target_admin = """class IsOrganizationAdmin(permissions.BasePermission):
    \"\"\"High permissions - accessible to Owners and Admins.\"\"\"
    def has_permission(self, request, view):
        org_id = extract_org_id(request, view)
        membership = get_member_membership(request, org_id)
        return membership is not None and membership.role in ['owner', 'admin']

    def has_object_permission(self, request, view, obj):
        org_id = extract_org_id(request, view, obj)
        membership = get_member_membership(request, org_id)
        return membership is not None and membership.role in ['owner', 'admin']"""

replacement_admin = """class IsOrganizationAdmin(permissions.BasePermission):
    \"\"\"High permissions - accessible to Owners and Admins.\"\"\"
    def has_permission(self, request, view):
        org_id = extract_org_id(request, view)
        membership = get_member_membership(request, org_id)
        if not membership: raise PermissionDenied("You are not an active member of this organization.")
        return membership.role in ['owner', 'admin']

    def has_object_permission(self, request, view, obj):
        org_id = extract_org_id(request, view, obj)
        membership = get_member_membership(request, org_id)
        if not membership: raise PermissionDenied("You are not an active member of this organization.")
        return membership.role in ['owner', 'admin']"""

content = content.replace(target_admin, replacement_admin)

# IsOrganizationMember
target_member = """class IsOrganizationMember(permissions.BasePermission):
    \"\"\"Basic tenant access - verifies the user is an active member of the tenant.\"\"\"
    def has_permission(self, request, view):
        org_id = extract_org_id(request, view)
        membership = get_member_membership(request, org_id)
        return membership is not None

    def has_object_permission(self, request, view, obj):
        org_id = extract_org_id(request, view, obj)
        membership = get_member_membership(request, org_id)
        return membership is not None"""

replacement_member = """class IsOrganizationMember(permissions.BasePermission):
    \"\"\"Basic tenant access - verifies the user is an active member of the tenant.\"\"\"
    def has_permission(self, request, view):
        org_id = extract_org_id(request, view)
        membership = get_member_membership(request, org_id)
        if not membership: raise PermissionDenied("You are not an active member of this organization.")
        return True

    def has_object_permission(self, request, view, obj):
        org_id = extract_org_id(request, view, obj)
        membership = get_member_membership(request, org_id)
        if not membership: raise PermissionDenied("You are not an active member of this organization.")
        return True"""

content = content.replace(target_member, replacement_member)


# HasGoalPermissions
target_goal = """        if not membership: return False"""
replacement_goal = """        if not membership: raise PermissionDenied("You are not an active member of this organization.")"""

content = content.replace(target_goal, replacement_goal)

with open('c:/Users/saura/ParseOps/backend/core/permissions.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("permissions.py patched to raise PermissionDenied.")
