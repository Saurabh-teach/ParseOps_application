from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import DashboardApp, WorkspaceApp
from .serializers import DashboardAppSerializer, WorkspaceAppSerializer
from organizations.models import Membership

class DashboardAppViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DashboardApp.objects.filter(is_active=True)
    serializer_class = DashboardAppSerializer
    permission_classes = [permissions.IsAuthenticated]

class WorkspaceAppViewSet(viewsets.ModelViewSet):
    serializer_class = WorkspaceAppSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        org_id = self.request.query_params.get('org_id')
        if not org_id:
            return WorkspaceApp.objects.none()
        return WorkspaceApp.objects.filter(organization_id=org_id)

    def perform_create(self, serializer):
        org = serializer.validated_data['organization']
        # Check if user is admin/owner of this org
        if not Membership.objects.filter(organization=org, user=self.request.user, role__in=['owner', 'admin']).exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only admins can install apps.")
        serializer.save()

    @action(detail=True, methods=['post'], url_path='toggle')
    def toggle_app(self, request, pk=None):
        workspace_app = self.get_object()
        # Check permissions
        if not Membership.objects.filter(organization=workspace_app.organization, user=request.user, role__in=['owner', 'admin']).exists():
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        workspace_app.is_enabled = not workspace_app.is_enabled
        workspace_app.save()
        return Response({"status": "success", "is_enabled": workspace_app.is_enabled})
