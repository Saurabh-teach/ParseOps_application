from django.db import models
from organizations.models import Organization

class DashboardApp(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='LayoutDashboard') # Lucide icon name
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class WorkspaceApp(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='installed_apps')
    app = models.ForeignKey(DashboardApp, on_delete=models.CASCADE)
    is_enabled = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, blank=True)
    installed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('organization', 'app')

    def __str__(self):
        return f"{self.app.name} in {self.organization.name}"
