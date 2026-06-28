import os

auto_register_snippet = """
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
"""

backend_dir = r"c:\Users\saura\ParseOps\backend"
app_names = ['analytics', 'chat', 'core', 'dashboard', 'goals', 'notes', 'notifications', 'organizations', 'profiles', 'tasks', 'users']

for app in app_names:
    admin_path = os.path.join(backend_dir, app, 'admin.py')
    if os.path.exists(admin_path):
        with open(admin_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if "Auto Register All Other Models" not in content:
            with open(admin_path, 'a', encoding='utf-8') as f:
                f.write(auto_register_snippet)
        print(f"Patched {app}/admin.py")
