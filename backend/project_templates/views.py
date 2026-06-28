from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import ProjectTemplate, TemplateFolder, TemplateItem, GoalFolder, GoalItem
from .serializers import ProjectTemplateSerializer, TemplateFolderSerializer, TemplateItemSerializer
from .services import TemplateService
from organizations.models import Organization
from goals.models import Goals

class IsOrganizationMember(permissions.BasePermission):
    def has_permission(self, request, view):
        org_slug = view.kwargs.get('org_slug')
        if not org_slug:
            return False
        return request.user.memberships.filter(organization__slug=org_slug, is_active=True).exists()

class ProjectTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizationMember]

    def get_queryset(self):
        org_slug = self.kwargs.get('org_slug')
        return ProjectTemplate.objects.filter(organization__slug=org_slug, is_active=True)

    def perform_create(self, serializer):
        org_slug = self.kwargs.get('org_slug')
        org = get_object_or_404(Organization, slug=org_slug)
        serializer.save(organization=org, created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def apply(self, request, org_slug=None, pk=None):
        template = self.get_object()
        goal_id = request.data.get('goal_id')
        if not goal_id:
            return Response({"error": "goal_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        goal = get_object_or_404(Goals, id=goal_id, organization__slug=org_slug)
        TemplateService.apply_template_to_goal(template, goal)
        return Response({"status": "Template applied successfully"})

    @action(detail=True, methods=['post'])
    def create_and_apply(self, request, org_slug=None, pk=None):
        template = self.get_object()
        org = get_object_or_404(Organization, slug=org_slug)
        
        goal_title = request.data.get('goal_title')
        if not goal_title:
            return Response({"error": "goal_title is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        goal_description = request.data.get('goal_description', '')
        due_date = request.data.get('due_date') or None
        priority = request.data.get('priority', 'medium')
        placeholders = request.data.get('placeholders', {})
        timeframe = request.data.get('timeframe', 'quarterly')
        
        # Replace placeholders in Goal details
        goal_title = TemplateService.replace_placeholders(goal_title, placeholders)
        goal_description = TemplateService.replace_placeholders(goal_description, placeholders)
        
        # Check if Goal with the same title already exists in the organization
        if Goals.objects.filter(organization=org, title=goal_title).exists():
            return Response(
                {"error": f"A goal with the title '{goal_title}' already exists in this organization."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Create Goal
        goal = Goals.objects.create(
            organization=org,
            title=goal_title,
            description=goal_description,
            owner=request.user,
            created_by=request.user,
            due_date=due_date,
            priority=priority,
            timeframe=timeframe,
            template_type='custom'
        )
        
        # Apply template with placeholders
        TemplateService.apply_template_to_goal(template, goal, placeholders, request.user)
        
        return Response({
            "status": "Goal created and template applied successfully",
            "goal_id": str(goal.id)
        }, status=status.HTTP_201_CREATED)
        
    @action(detail=False, methods=['post'])
    def save_from_goal(self, request, org_slug=None):
        goal_id = request.data.get('goal_id')
        template_name = request.data.get('name', 'New Template')
        
        goal = get_object_or_404(Goals, id=goal_id, organization__slug=org_slug)
        org = get_object_or_404(Organization, slug=org_slug)
        
        template = TemplateService.create_template_from_goal(goal, org, template_name, request.user)
            
        return Response({"status": "Template saved successfully", "template_id": template.id})

class TemplateFolderViewSet(viewsets.ModelViewSet):
    serializer_class = TemplateFolderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizationMember]

    def get_queryset(self):
        org_slug = self.kwargs.get('org_slug')
        return TemplateFolder.objects.filter(template__organization__slug=org_slug)

class TemplateItemViewSet(viewsets.ModelViewSet):
    serializer_class = TemplateItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizationMember]

    def get_queryset(self):
        org_slug = self.kwargs.get('org_slug')
        return TemplateItem.objects.filter(folder__template__organization__slug=org_slug)
