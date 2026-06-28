from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DashboardAppViewSet, WorkspaceAppViewSet

router = DefaultRouter()
router.register(r'available-apps', DashboardAppViewSet)
router.register(r'workspace-apps', WorkspaceAppViewSet, basename='workspace-app')

urlpatterns = [
    path('', include(router.urls)),
]
