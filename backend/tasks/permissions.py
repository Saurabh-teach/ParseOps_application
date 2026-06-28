from rest_framework import permissions
from core.permissions import get_member_membership, has_granular_permission

class IsOrganizationMember(permissions.BasePermission):
    """
    Verifies that the user is an active member of the organization context.
    """
    def has_permission(self, request, view):
        print(f"DEBUG IsOrganizationMember.has_permission: user={request.user}, kwargs={view.kwargs}")
        if 'task_id' in view.kwargs or 'comment_id' in view.kwargs:
            print("DEBUG: task_id or comment_id in view.kwargs -> True")
            return True
        org_id = request.query_params.get('organization') or request.data.get('organization') or view.kwargs.get('org_id')
        membership = get_member_membership(request, org_id)
        result = membership is not None and membership.is_active
        print(f"DEBUG: org_id={org_id}, membership={membership}, result={result}")
        return result

    def has_object_permission(self, request, view, obj):
        print(f"DEBUG IsOrganizationMember.has_object_permission: user={request.user}, obj={obj}")
        org = getattr(obj, 'organization', None)
        if not org and hasattr(obj, 'task'):
            org = getattr(obj.task, 'organization', None)
        if not org:
            print("DEBUG: no organization on obj -> False")
            return False
        membership = get_member_membership(request, org.id)
        result = membership is not None and membership.is_active
        print(f"DEBUG: org.id={org.id}, membership={membership}, result={result}")
        return result


class CanCreateTask(permissions.BasePermission):
    """
    Checks if a user is allowed to create tasks:
    - Owners, Admins, and members with 'can_create_tasks' permission.
    """
    def has_permission(self, request, view):
        org_id = request.query_params.get('organization') or request.data.get('organization') or view.kwargs.get('org_id')
        membership = get_member_membership(request, org_id)
        if not membership or not membership.is_active:
            return False
        return has_granular_permission(membership, 'can_create_tasks')


class CanEditTask(permissions.BasePermission):
    """
    Determines if a user has access to edit/update a task:
    - Owner/Admin: Can edit any task in the organization.
    - Member: Can edit if they are the creator, an assignee, owner of the linked Goal, or have custom permission.
    """
    def has_permission(self, request, view):
        # We check details in has_object_permission
        return True

    def has_object_permission(self, request, view, obj):
        membership = get_member_membership(request, obj.organization.id)
        if not membership or not membership.is_active:
            return False

        # Owner and Admin can edit anything
        if membership.role in ['owner', 'admin']:
            return True

        # Member specific edit logic
        is_creator = obj.created_by == request.user
        is_assignee = obj.assignee_id == request.user.id
        is_goal_owner = obj.goal and obj.goal.owner == request.user

        is_allowed = is_creator or is_assignee or is_goal_owner
        return is_allowed and has_granular_permission(membership, 'can_edit_tasks')


class CanDeleteTask(permissions.BasePermission):
    """
    Controls deletion of tasks:
    - Owner/Admin: Can delete any task.
    - Member: Can delete ONLY if they are the creator of the task AND have granular permission.
    """
    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        print(f"DEBUG CanDeleteTask.has_object_permission: user={request.user}, obj={obj}")
        membership = get_member_membership(request, obj.organization.id)
        if not membership or not membership.is_active:
            print("DEBUG: no active membership -> False")
            return False

        # Owner and Admin can delete anything
        if membership.role in ['owner', 'admin']:
            print(f"DEBUG: role={membership.role} -> True")
            return True

        # Member can only delete if they created it AND they have granular permission
        result = obj.created_by == request.user and has_granular_permission(membership, 'can_delete_tasks')
        print(f"DEBUG: created_by={obj.created_by}, is_creator={obj.created_by == request.user}, result={result}")
        return result
