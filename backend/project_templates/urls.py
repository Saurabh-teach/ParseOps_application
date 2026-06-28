from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectTemplateViewSet, TemplateFolderViewSet, TemplateItemViewSet
from .import_views import TemplateCSVImportView

router = DefaultRouter()
router.register(r'templates', ProjectTemplateViewSet, basename='templates')
router.register(r'folders', TemplateFolderViewSet, basename='template-folders')
router.register(r'items', TemplateItemViewSet, basename='template-items')

urlpatterns = [
    path('templates/import-file/', TemplateCSVImportView.as_view(), name='template-import-file'),
    path('', include(router.urls)),
]

