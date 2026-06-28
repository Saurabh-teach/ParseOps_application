from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, SaveWebPushSubscriptionView

router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification')

urlpatterns = [
    path('webpush-subscribe/', SaveWebPushSubscriptionView.as_view(), name='webpush-subscribe'),
    path('', include(router.urls)),
]
