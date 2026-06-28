from django.urls import path, include
from rest_framework.routers import DefaultRouter
from goals.views import GoalViewSet, KeyResultViewSet

router = DefaultRouter()
router.register(r'', GoalViewSet, basename='goal')

urlpatterns = [
    # Key Results Nested Routes
    path('<uuid:goal_id>/key-results/', KeyResultViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='goal-key-results-list'),
    
    path('<uuid:goal_id>/key-results/<uuid:pk>/', KeyResultViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='goal-key-results-detail'),

    # Goals Standard Routes
    path('', include(router.urls)),
]
