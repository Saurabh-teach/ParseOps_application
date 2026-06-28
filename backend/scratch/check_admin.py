import django
import os
import sys

# Set up Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.apps import apps
from django.contrib import admin

unreg = []
for app in apps.get_app_configs():
    if app.name.startswith('django.') or app.name in ['rest_framework', 'drf_spectacular', 'rest_framework_simplejwt', 'corsheaders', 'channels', 'rest_framework_simplejwt.token_blacklist']:
        continue
    
    for model in app.get_models():
        if not admin.site.is_registered(model):
            unreg.append(f"{app.name}.{model.__name__}")

print('UNREGISTERED:', unreg)
