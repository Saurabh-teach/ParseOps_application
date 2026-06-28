from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Return notifications belonging to the logged-in user, ordered by newest first
        queryset = Notification.objects.filter(user=self.request.user).order_by('-created_at')
        org_slug = self.request.query_params.get('org')
        if org_slug:
            queryset = queryset.filter(organization__slug=org_slug)
        return queryset

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"message": "All notifications marked as read"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({"message": "Notification marked as read"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'], url_path='clear')
    def clear(self, request, pk=None):
        notification = self.get_object()
        notification.delete()
        return Response({"message": "Notification cleared"}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['delete'], url_path='clear-all')
    def clear_all(self, request):
        self.get_queryset().delete()
        return Response({"message": "All notifications cleared"}, status=status.HTTP_204_NO_CONTENT)

from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .models import WebPushSubscription
from .serializers import WebPushSubscriptionSerializer

class SaveWebPushSubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=['Notifications'],
        summary="Save Web Push Subscription",
        description="Saves or updates a browser's Web Push Notification subscription credentials for the logged-in user.",
        request=WebPushSubscriptionSerializer,
        responses={
            201: OpenApiResponse(description="Subscription saved successfully"),
            200: OpenApiResponse(description="Subscription updated successfully"),
            400: OpenApiResponse(description="Invalid payload")
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = WebPushSubscriptionSerializer(data=request.data)
        if serializer.is_valid():
            # Check if this endpoint already exists for the user
            endpoint = serializer.validated_data.get('endpoint')
            sub, created = WebPushSubscription.objects.update_or_create(
                endpoint=endpoint,
                defaults={
                    'user': request.user,
                    'p256dh': serializer.validated_data.get('p256dh'),
                    'auth': serializer.validated_data.get('auth')
                }
            )
            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            return Response({"message": "Subscription saved"}, status=status_code)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
