from rest_framework import permissions
from .models import OrganizationMembership

class IsOrganizationOwner(permissions.BasePermission):
    """
    Allows access only to the owner of the organization.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Handle both Organization itself and related organization-scoped models
        from .models import Organization
        org = obj if isinstance(obj, Organization) else getattr(obj, 'organization', None)
        if not org:
            return False
        return OrganizationMembership.objects.filter(
            organization=org, 
            user=request.user, 
            role='owner', 
            is_active=True
        ).exists()

class IsOrganizationAdmin(permissions.BasePermission):
    """
    Allows access only to owners or admins of the organization.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        from .models import Organization
        org = obj if isinstance(obj, Organization) else getattr(obj, 'organization', None)
        if not org:
            return False
        return OrganizationMembership.objects.filter(
            organization=org, 
            user=request.user, 
            role__in=['owner', 'admin'], 
            is_active=True
        ).exists()

class IsOrganizationMember(permissions.BasePermission):
    """
    Allows access to any active member of the organization.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        from .models import Organization
        org = obj if isinstance(obj, Organization) else getattr(obj, 'organization', None)
        if not org:
            return False
        return OrganizationMembership.objects.filter(
            organization=org, 
            user=request.user, 
            is_active=True
        ).exists()
