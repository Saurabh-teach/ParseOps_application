from django.urls import path
from .views import DashboardAnalyticsView

urlpatterns = [
    path("org/<uuid:org_id>/", DashboardAnalyticsView.as_view(), name="org-dashboard-analytics"),
]
