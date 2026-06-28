from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Note
from .serializers import NoteSerializer

class NoteViewSet(viewsets.ModelViewSet):
    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Note.objects.filter(user=self.request.user)
        
        org_id = self.request.query_params.get('organization')
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
            
        return queryset.order_by('-updated_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
