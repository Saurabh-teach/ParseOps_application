from rest_framework.exceptions import PermissionDenied
from rest_framework import permissions
from organizations.models import OrganizationMembership

def get_member_membership(request, org_id):
    """
    Helper to fetch the active membership for a given user and organization.
    """
    if not request.user or not request.user.is_authenticated or not org_id:
        return None
    return OrganizationMembership.objects.filter(
        organization_id=org_id,
        user=request.user,
        is_active=True
    ).first()

def has_granular_permission(membership, permission_key):
    """
    Checks if a membership holds a specific permission, respecting role-based defaults
    and explicit custom permission overrides.
    """
    if not membership or not membership.is_active:
        return False
    
    # Owner always has absolute full control
    if membership.role == 'owner':
        return True
        
    # Custom explicit overrides take priority for Admin and Member
    if membership.custom_permissions and permission_key in membership.custom_permissions:
        return bool(membership.custom_permissions[permission_key])
        
    # Admin defaults (can do almost everything)
    if membership.role == 'admin':
        return True # Handled exceptions (like changing Owner role) are done at object level
        
    # Member defaults (restricted access)
    if membership.role == 'member':
        defaults = {
            # Goals
            'create_workspace_goals': True,
            'view_all_goals': False, 
            'edit_goals': False, 
            'delete_workspace_goals': False,
            'manage_goal_visibility': False,
            'assign_goals': False,
            
            # Tasks
            'create_workspace_tasks': True,
            'view_all_tasks': False,
            'edit_tasks': False,
            'delete_workspace_tasks': False,
            'manage_task_visibility': False,
            'assign_tasks': False,
            'manage_task_comments': True,
            'manage_task_attachments': True,
            
            # Team & Org
            'invite_workspace_members': False,
            'remove_workspace_members': False,
            'change_roles': False,
            'view_member_profiles': True,
            'manage_workspace_settings': False
        }
        return defaults.get(permission_key, False)
        
    return False

def extract_org_id(request, view, obj=None):
    """Helper to intelligently extract org_id from request, view kwargs, or object"""
    # From query params or body
    org_id = request.query_params.get('organization') or request.data.get('organization')
    if org_id: return org_id
    
    # From URL kwargs
    org_id = view.kwargs.get('org_id')
    if org_id: return org_id
    
    # Try resolving via slug if present
    org_slug = view.kwargs.get('org_slug')
    if org_slug:
        from organizations.models import Organization
        try:
            return Organization.objects.filter(slug=org_slug).values_list('id', flat=True).first()
        except Exception:
            pass
            
    # From object
    if obj:
        if hasattr(obj, 'organization_id'):
            return obj.organization_id
        if hasattr(obj, 'organization') and obj.organization:
            return obj.organization.id
            
    # Try from view.get_object() if not provided directly
    if hasattr(view, 'get_object') and obj is None:
        try:
            instance = view.get_object()
            if hasattr(instance, 'organization_id'): return instance.organization_id
        except Exception:
            pass

    # Resolve from task_id in URL kwargs (e.g. GET /api/tasks/{task_id}/)
    task_id = view.kwargs.get('task_id')
    if task_id:
        from tasks.models import Task
        try:
            return Task.objects.filter(id=task_id).values_list('organization_id', flat=True).first()
        except Exception:
            pass

    # Resolve from comment_id in URL kwargs (e.g. GET /api/comments/{comment_id}/)
    comment_id = view.kwargs.get('comment_id')
    if comment_id:
        from tasks.models import TaskComment
        try:
            return TaskComment.objects.filter(id=comment_id).values_list('task__organization_id', flat=True).first()
        except Exception:
            pass
            
    return None


class IsOrganizationOwner(permissions.BasePermission):
    """Full permissions - only accessible to organization Owners."""
    def has_permission(self, request, view):
        org_id = extract_org_id(request, view)
        membership = get_member_membership(request, org_id)
        if not membership: raise PermissionDenied("You are not an active member of this organization.")
        return membership.role == 'owner'

    def has_object_permission(self, request, view, obj):
        org_id = extract_org_id(request, view, obj)
        membership = get_member_membership(request, org_id)
        if not membership: raise PermissionDenied("You are not an active member of this organization.")
        return membership.role == 'owner'

class IsOrganizationAdmin(permissions.BasePermission):
    """High permissions - accessible to Owners and Admins."""
    def has_permission(self, request, view):
        org_id = extract_org_id(request, view)
        membership = get_member_membership(request, org_id)
        if not membership: raise PermissionDenied("You are not an active member of this organization.")
        return membership.role in ['owner', 'admin']

    def has_object_permission(self, request, view, obj):
        org_id = extract_org_id(request, view, obj)
        membership = get_member_membership(request, org_id)
        if not membership: raise PermissionDenied("You are not an active member of this organization.")
        return membership.role in ['owner', 'admin']

class IsOrganizationMember(permissions.BasePermission):
    """Basic tenant access - verifies the user is an active member of the tenant."""
    def has_permission(self, request, view):
        org_id = extract_org_id(request, view)
        membership = get_member_membership(request, org_id)
        if not membership: raise PermissionDenied("You are not an active member of this organization.")
        return True

    def has_object_permission(self, request, view, obj):
        org_id = extract_org_id(request, view, obj)
        membership = get_member_membership(request, org_id)
        if not membership: raise PermissionDenied("You are not an active member of this organization.")
        return True

class HasGoalPermissions(permissions.BasePermission):
    """
    Comprehensive Role-Based Access Control for Goals
    """
    def has_permission(self, request, view):
        org_id = extract_org_id(request, view)
        membership = get_member_membership(request, org_id)
        if not membership: raise PermissionDenied("You are not an active member of this organization.")
        
        if request.method == 'POST':
            return has_granular_permission(membership, 'create_workspace_goals')
            
        return True # SAFE_METHODS and object-level checks handle the rest

    def has_object_permission(self, request, view, obj):
        org_id = extract_org_id(request, view, obj)
        membership = get_member_membership(request, org_id)
        if not membership: raise PermissionDenied("You are not an active member of this organization.")
        
        user = request.user
        
        # Check basic viewing privileges based on sharing_option
        is_creator = (getattr(obj, 'created_by', None) == user)
        is_owner = (getattr(obj, 'owner', None) == user)
        is_assignee = obj.assignees.filter(id=user.id).exists() if hasattr(obj, 'assignees') else False
        is_viewer = obj.shared_viewers.filter(id=user.id).exists() if hasattr(obj, 'shared_viewers') else False
        
        if request.method in permissions.SAFE_METHODS:
            if has_granular_permission(membership, 'view_all_goals'):
                return True
            if is_creator or is_owner:
                return True
            sharing = getattr(obj, 'sharing_option', 'organization')
            if sharing == 'organization': return True
            if sharing == 'specific': return is_assignee or is_viewer
            if sharing == 'private': return is_assignee
            return False
            
        if request.method == 'DELETE':
            # Creator can delete their own if they have basic delete privileges, 
            # Or if they have organization-wide delete privilege
            if has_granular_permission(membership, 'delete_workspace_goals'): return True
            return False # Strictly rely on override/role
            
        if request.method in ['PUT', 'PATCH']:
            # 1. Check for explicit custom override block
            if membership.custom_permissions and membership.custom_permissions.get('edit_goals') is False:
                return False
                
            # 2. If they have permission (Admin/Owner or explicit override to True), they can edit everything
            if has_granular_permission(membership, 'edit_goals'):
                return True
                
            # 3. Otherwise (normal Member default), they can only edit their own goals
            if is_creator or is_owner or is_assignee:
                # Assignee/Creator cannot change visibility/sharing without manage_goal_visibility
                if not has_granular_permission(membership, 'manage_goal_visibility'):
                    if 'sharing_option' in request.data or 'shared_viewers' in request.data:
                        return False
                # Assignee/Creator cannot change assignees/owner without assign_goals
                if not has_granular_permission(membership, 'assign_goals'):
                    if 'assignees' in request.data or 'owner' in request.data:
                        return False
                return True
                
        return False

class HasTaskPermissions(permissions.BasePermission):
    """
    Comprehensive Role-Based Access Control for Tasks
    """
    def has_permission(self, request, view):
        org_id = extract_org_id(request, view)
        membership = get_member_membership(request, org_id)
        if not membership: raise PermissionDenied("You are not an active member of this organization.")
        
        if request.method == 'POST':
            return has_granular_permission(membership, 'create_workspace_tasks')
            
        return True

    def has_object_permission(self, request, view, obj):
        org_id = extract_org_id(request, view, obj)
        membership = get_member_membership(request, org_id)
        if not membership: raise PermissionDenied("You are not an active member of this organization.")
        
        user = request.user
        
        is_creator = (getattr(obj, 'created_by', None) == user)
        is_assignee = obj.assignees.filter(id=user.id).exists() if hasattr(obj, 'assignees') else False
        is_viewer = obj.shared_viewers.filter(id=user.id).exists() if hasattr(obj, 'shared_viewers') else False
        
        if request.method in permissions.SAFE_METHODS:
            if has_granular_permission(membership, 'view_all_tasks'): return True
            if is_creator: return True
            
            sharing = getattr(obj, 'sharing_option', 'organization')
            if sharing == 'organization': return True
            if sharing == 'specific': return is_assignee or is_viewer
            if sharing == 'private': return is_assignee
            return False
            
        if request.method == 'DELETE':
            return has_granular_permission(membership, 'delete_workspace_tasks')
            
        if request.method in ['PUT', 'PATCH']:
            # Allow creators/assignees to update task status (and status only)
            is_status_only_update = False
            if isinstance(request.data, dict) and set(request.data.keys()).issubset({'status'}):
                is_status_only_update = True
                
            if is_status_only_update and (is_assignee or is_creator):
                return True
                
            # Task Creator owns the task and can edit details
            if is_creator:
                return True

            # 2. If they have permission (Admin/Owner or explicit override to True), they can edit details
            if has_granular_permission(membership, 'edit_tasks'):
                # Cannot change visibility/sharing without manage_task_visibility
                if not has_granular_permission(membership, 'manage_task_visibility'):
                    if 'sharing_option' in request.data or 'visible_to' in request.data or 'watchers' in request.data:
                        return False
                # Cannot change assignees without assign_tasks
                if not has_granular_permission(membership, 'assign_tasks'):
                    if 'assignees' in request.data:
                        return False
                return True
                
            # 3. Standard members without explicit edit_tasks permission cannot edit other details
            return False
            
        return False

class HasTeamPermissions(permissions.BasePermission):
    """
    Permissions for Workspace Settings and Member Management
    """
    def has_permission(self, request, view):
        org_id = extract_org_id(request, view)
        membership = get_member_membership(request, org_id)
        if not membership: raise PermissionDenied("You are not an active member of this organization.")
        
        if request.method in permissions.SAFE_METHODS:
            return has_granular_permission(membership, 'view_member_profiles')
            
        if request.method == 'POST': # Inviting
            return has_granular_permission(membership, 'invite_workspace_members')
            
        if request.method == 'DELETE': # Removing
            return has_granular_permission(membership, 'remove_workspace_members')
            
        if request.method in ['PUT', 'PATCH']: # Changing roles / settings
            if 'role' in request.data or 'custom_permissions' in request.data:
                return has_granular_permission(membership, 'change_roles')
            return has_granular_permission(membership, 'manage_workspace_settings')
            
        return False

    def has_object_permission(self, request, view, obj):
        org_id = extract_org_id(request, view, obj)
        membership = get_member_membership(request, org_id)
        if not membership: raise PermissionDenied("You are not an active member of this organization.")
        
        if request.method == 'DELETE' or ('role' in request.data):
            # No one, not even Admin, can remove or change the role of an Owner, except the Owner themselves
            # Usually handled by strict view logic, but good to add an extra layer
            target_role = getattr(obj, 'role', None)
            if target_role == 'owner' and membership.role != 'owner':
                return False
                
        return True
