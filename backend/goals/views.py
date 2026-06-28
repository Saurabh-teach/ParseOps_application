from rest_framework import viewsets, permissions, status
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError

from goals.models import Goals, KeyResult
from goals.serializers import (
    GoalListSerializer, GoalDetailSerializer, GoalCreateUpdateSerializer, KeyResultSerializer
)
from organizations.models import Organization, OrganizationMembership
from core.permissions import HasGoalPermissions, get_member_membership

class GoalViewSet(viewsets.ModelViewSet):
    """
    Enterprise-grade Goal ViewSet with robust access control, role-based checks,
    visibility filtering, soft-delete, and restore actions.
    """
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), HasGoalPermissions()]
        elif self.action in ['update', 'partial_update', 'destroy', 'restore']:
            return [permissions.IsAuthenticated(), HasGoalPermissions()]
        return [permissions.IsAuthenticated(), HasGoalPermissions()]

    def get_serializer_class(self):
        if self.action == 'list':
            return GoalListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return GoalCreateUpdateSerializer
        return GoalDetailSerializer

    def get_queryset(self):
        org_id = self.request.query_params.get('organization') or self.kwargs.get('org_id')
        if not org_id:
            return Goals.objects.filter(is_deleted=False)

        # Ensure user is an active member of this organization
        membership = OrganizationMembership.objects.filter(
            organization_id=org_id,
            user=self.request.user,
            is_active=True
        ).first()

        if not membership:
            raise PermissionDenied("You are not an active member of this organization.")

        queryset = Goals.objects.filter(organization_id=org_id, is_deleted=False)

        if membership.role in ['owner', 'admin']:
            return queryset.order_by('-created_at')

        queryset = queryset.filter(
            Q(visibility_type='organization') |
            Q(sharing_option='organization') |
            Q(created_by=self.request.user) |
            Q(owner=self.request.user) |
            Q(visible_to=self.request.user) |
            Q(assignees=self.request.user) |
            Q(shared_viewers=self.request.user)
        ).distinct()

        return queryset.order_by('-created_at')

    @transaction.atomic
    def perform_create(self, serializer):
        org_id = self.request.query_params.get('organization') or self.kwargs.get('org_id')
        if not org_id:
            raise ValidationError({"organization": "Organization parameter is required."})

        org = get_object_or_404(Organization, id=org_id)
        membership = get_object_or_404(
            OrganizationMembership,
            organization=org,
            user=self.request.user,
            is_active=True
        )

        owner = serializer.validated_data.get('owner', self.request.user)

        # Standard members cannot assign goals to owners or admins
        if membership.role == 'member' and owner != self.request.user:
            owner_membership = OrganizationMembership.objects.filter(
                organization=org,
                user=owner,
                is_active=True
            ).first()
            if owner_membership and owner_membership.role in ['owner', 'admin']:
                raise PermissionDenied("Regular members cannot assign goals to Admins or Owners.")

        goal = serializer.save(
            organization=org,
            created_by=self.request.user,
            owner=owner
        )

        if goal.visibility_type == 'specific':
            goal.visible_to.add(self.request.user)
            if owner:
                goal.visible_to.add(owner)
            
            management_users = OrganizationMembership.objects.filter(
                organization=org,
                role__in=['owner', 'admin'],
                is_active=True
            ).values_list('user_id', flat=True)
            goal.visible_to.add(*management_users)

        if goal.visibility_type == 'specific':
            allowed_user_ids = goal.visible_to.values_list('id', flat=True)
            active_memberships = OrganizationMembership.objects.filter(
                organization=org,
                is_active=True,
                user_id__in=allowed_user_ids
            ).exclude(user=self.request.user)
        else:
            active_memberships = OrganizationMembership.objects.filter(
                organization=org,
                is_active=True
            ).exclude(user=self.request.user)

        from notifications.models import Notification
        for mem in active_memberships:
            Notification.objects.create(
                user=mem.user,
                organization=org,
                title=f"New Goal: {goal.title}",
                message=f"{self.request.user.email} created a new goal: '{goal.title}' in {org.name}",
                notification_type='goal_created',
                data={
                    "organization_id": str(org.id),
                    "goal_id": str(goal.id),
                    "goal_title": goal.title,
                }
            )

    def perform_update(self, serializer):
        goal = self.get_object()
        membership = get_object_or_404(
            OrganizationMembership,
            organization=goal.organization,
            user=self.request.user,
            is_active=True
        )

        if membership.role in ['owner', 'admin']:
            serializer.save()
            return

        if goal.created_by != self.request.user and goal.owner != self.request.user:
            raise PermissionDenied("You do not have permission to modify this goal.")

        serializer.save()

    def perform_destroy(self, instance):
        membership = get_object_or_404(
            OrganizationMembership,
            organization=instance.organization,
            user=self.request.user,
            is_active=True
        )

        if membership.role in ['owner', 'admin']:
            instance.delete()
            return

        if instance.created_by != self.request.user:
            raise PermissionDenied("Only workspace administrators or the goal creator can delete this goal.")

        instance.delete()

    @action(detail=True, methods=['post'], url_path='restore')
    def restore(self, request, pk=None):
        """
        Custom endpoint to restore a soft-deleted goal.
        """
        goal = get_object_or_404(Goals, pk=pk)
        membership = get_object_or_404(
            OrganizationMembership,
            organization=goal.organization,
            user=request.user,
            is_active=True
        )

        if membership.role == 'member' and goal.created_by != request.user:
            raise PermissionDenied("Only workspace administrators or the goal creator can restore this goal.")

        goal.restore()
        return Response({"message": "Goal restored successfully!"}, status=status.HTTP_200_OK)

class KeyResultViewSet(viewsets.ModelViewSet):
    """
    Sub-viewset to handle nested Key Results for OKRs.
    """
    serializer_class = KeyResultSerializer
    permission_classes = [IsAuthenticated, HasGoalPermissions]

    def get_queryset(self):
        goal_id = self.kwargs.get('goal_id')
        if not goal_id:
            return KeyResult.objects.none()

        goal = get_object_or_404(Goals, id=goal_id, is_deleted=False)
        
        membership = get_object_or_404(
            OrganizationMembership,
            organization=goal.organization,
            user=self.request.user,
            is_active=True
        )

        if membership.role == 'member':
            can_see = Goals.objects.filter(id=goal_id).filter(
                Q(visibility_type='organization') |
                Q(created_by=self.request.user) |
                Q(owner=self.request.user) |
                Q(visible_to=self.request.user)
            ).exists()
            if not can_see:
                raise PermissionDenied("You do not have access to this goal's Key Results.")

        return KeyResult.objects.filter(goal_id=goal_id).order_by('created_at')

    @transaction.atomic
    def perform_create(self, serializer):
        goal_id = self.kwargs.get('goal_id')
        goal = get_object_or_404(Goals, id=goal_id, is_deleted=False)
        
        membership = get_object_or_404(
            OrganizationMembership,
            organization=goal.organization,
            user=self.request.user,
            is_active=True
        )

        if membership.role == 'member' and goal.created_by != self.request.user and goal.owner != self.request.user:
            raise PermissionDenied("You do not have permission to add Key Results to this goal.")

        serializer.save(goal=goal)

    def perform_update(self, serializer):
        kr = self.get_object()
        membership = get_object_or_404(
            OrganizationMembership,
            organization=kr.goal.organization,
            user=self.request.user,
            is_active=True
        )

        if membership.role == 'member' and kr.goal.created_by != self.request.user and kr.goal.owner != self.request.user:
            raise PermissionDenied("You do not have permission to edit this Key Result.")

        serializer.save()

    def perform_destroy(self, instance):
        membership = get_object_or_404(
            OrganizationMembership,
            organization=instance.goal.organization,
            user=self.request.user,
            is_active=True
        )

        if membership.role == 'member' and instance.goal.created_by != self.request.user:
            raise PermissionDenied("You do not have permission to delete this Key Result.")

        instance.delete()


from rest_framework import generics

class OrgSlugMixin:
    def get_organization(self):
        org_slug = self.kwargs.get('org_slug')
        return get_object_or_404(Organization, slug=org_slug)

class OrgGoalListView(OrgSlugMixin, generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, HasGoalPermissions]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return GoalCreateUpdateSerializer
        return GoalListSerializer

    def get_queryset(self):
        org = self.get_organization()
        user = self.request.user
        queryset = Goals.objects.filter(organization=org, is_deleted=False)
        
        membership = get_member_membership(self.request, org.id)
        if not membership or not membership.is_active:
            raise PermissionDenied("You are not an active member of this organization.")

        if membership.role in ['owner', 'admin']:
            return queryset.order_by('-created_at')

        from django.db.models import Q
        return queryset.filter(
            Q(sharing_option='organization') |
            Q(sharing_option='specific', assignees=user) |
            Q(sharing_option='specific', shared_viewers=user) |
            Q(sharing_option='private', assignees=user) |
            Q(created_by=user) |
            Q(owner=user)
        ).distinct().order_by('-created_at')

    @transaction.atomic
    def perform_create(self, serializer):
        org = self.get_organization()
        serializer.save(
            organization=org,
            created_by=self.request.user
        )

class OrgGoalDetailView(OrgSlugMixin, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, HasGoalPermissions]
    queryset = Goals.objects.filter(is_deleted=False)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return GoalCreateUpdateSerializer
        return GoalDetailSerializer

    def perform_destroy(self, instance):
        instance.delete()
