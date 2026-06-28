from rest_framework import permissions
from core.permissions import get_member_membership, has_granular_permission

class IsOrganizationMember(permissions.BasePermission):
    """
    Ensures the user is an active member of the target organization.
    """
    def has_permission(self, request, view):
        if getattr(view, 'detail', False) or 'pk' in view.kwargs:
            return True
        org_id = request.query_params.get('organization') or request.data.get('organization') or view.kwargs.get('org_id')
        membership = get_member_membership(request, org_id)
        return membership is not None and membership.is_active

    def has_object_permission(self, request, view, obj):
        org = obj if hasattr(obj, 'name') else getattr(obj, 'organization', None)
        if not org:
            return False
        membership = get_member_membership(request, org.id)
        if membership is None or not membership.is_active:
            return False

        # Owners and admins always have full access to any goal (hierarchy override)
        if membership.role in ['owner', 'admin']:
            return True

        # For specific-visibility goals: only grant access if user is in visible_to, shared_viewers, assignees, or is creator/owner
        if hasattr(obj, 'visibility_type') and (obj.visibility_type == 'specific' or getattr(obj, 'sharing_option', '') == 'specific'):
            is_visible = False
            if hasattr(obj, 'visible_to') and obj.visible_to.filter(id=request.user.id).exists():
                is_visible = True
            if hasattr(obj, 'shared_viewers') and obj.shared_viewers.filter(id=request.user.id).exists():
                is_visible = True
            if hasattr(obj, 'assignees') and obj.assignees.filter(id=request.user.id).exists():
                is_visible = True
            if getattr(obj, 'created_by', None) == request.user or getattr(obj, 'owner', None) == request.user:
                is_visible = True
            
            if not is_visible:
                return False

        return True

class CanManageGoals(permissions.BasePermission):
    """
    Determines if a user has permission to create new goals in the workspace.
    """
    def has_permission(self, request, view):
        org_id = request.query_params.get('organization') or request.data.get('organization') or view.kwargs.get('org_id')
        membership = get_member_membership(request, org_id)
        return membership is not None and membership.is_active and has_granular_permission(membership, 'can_create_goals')

class CanEditGoal(permissions.BasePermission):
    """
    Checks if a user can edit/delete a specific goal:
    - Owners and Admins can manage any goal
    - Members can edit if they are an assignee, creator, owner, or have custom permission
    - Members cannot delete goals created by others
    """
    def has_permission(self, request, view):
        if getattr(view, 'detail', False) or 'pk' in view.kwargs:
            return True
        org_id = request.query_params.get('organization') or request.data.get('organization') or view.kwargs.get('org_id')
        membership = get_member_membership(request, org_id)
        return membership is not None and membership.is_active

    def has_object_permission(self, request, view, obj):
        membership = get_member_membership(request, obj.organization.id)
        if not membership or not membership.is_active:
            return False
            
        # Owner & Admin can edit/delete anything
        if membership.role in ['owner', 'admin']:
            return True
            
        # Member specific permissions
        is_creator_or_owner = (obj.created_by == request.user or obj.owner == request.user)
        is_assignee = False
        if hasattr(obj, 'assignees') and obj.assignees.filter(id=request.user.id).exists():
            is_assignee = True
        
        if request.method in permissions.SAFE_METHODS:
            return True # Let other permissions handle basic visibility filtering
            
        if request.method == 'DELETE':
            # Members can NEVER delete goals created by others
            return obj.created_by == request.user and has_granular_permission(membership, 'can_delete_goals')
            
        # Edit/Update
        return (is_creator_or_owner or is_assignee) and has_granular_permission(membership, 'can_edit_goals')
