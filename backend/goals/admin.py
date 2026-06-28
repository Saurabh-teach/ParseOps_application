from django.contrib import admin
from .models import Goals, KeyResult

@admin.register(Goals)
class GoalsAdmin(admin.ModelAdmin):
    list_display = ('title', 'organization', 'owner', 'status', 'priority', 'progress', 'is_active', 'created_at')
    list_filter = ('status', 'priority', 'is_active', 'is_deleted')
    search_fields = ('title', 'description', 'organization__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)

@admin.register(KeyResult)
class KeyResultAdmin(admin.ModelAdmin):
    list_display = ('title', 'goal', 'current_value', 'target_value', 'unit')
    list_filter = ('goal__organization',)
    search_fields = ('title', 'goal__title')
    readonly_fields = ('id', 'created_at', 'updated_at')

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
