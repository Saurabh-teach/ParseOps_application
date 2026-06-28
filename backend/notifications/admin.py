from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__email', 'title', 'message')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at')

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
