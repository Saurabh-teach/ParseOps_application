from django.contrib import admin
from .models import DashboardApp, WorkspaceApp

@admin.register(DashboardApp)
class DashboardAppAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description', 'icon', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'slug', 'description')
    ordering = ('name',)

@admin.register(WorkspaceApp)
class WorkspaceAppAdmin(admin.ModelAdmin):
    list_display = ('organization', 'app', 'is_enabled', 'installed_at')
    list_filter = ('is_enabled', 'installed_at')
    search_fields = ('organization__name', 'app__name')
    ordering = ('-installed_at',)

# --- Auto Register All Other Models ---
import os
from django.apps import apps
from django.contrib import admin

_app_name = os.path.basename(os.path.dirname(__file__))
try:
    _app = apps.get_app_config(_app_name)
    for _model in _app.get_models():
        try:
            class _DynamicModelAdmin(admin.ModelAdmin):
                list_display = [f.name for f in _model._meta.fields]
            admin.site.register(_model, _DynamicModelAdmin)
        except admin.sites.AlreadyRegistered:
            pass
except Exception:
    pass
