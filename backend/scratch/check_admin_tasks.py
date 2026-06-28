import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tasks.models import Task
from django.contrib.auth import get_user_model

User = get_user_model()
admin = User.objects.get(email="admin@gmail.com")

print("=" * 80)
print(f"ALL ACTIVE TASKS ASSIGNED TO {admin.email} ACROSS ALL ORGANIZATIONS")
print("=" * 80)

active_tasks = admin.assigned_tasks.exclude(status='done')
total_hours = 0.0
for t in active_tasks:
    hours = 0.0
    if t.estimated_hours is not None and t.estimated_hours > 0:
        hours = float(t.estimated_hours)
    elif t.estimated_minutes is not None and t.estimated_minutes > 0:
        hours = t.estimated_minutes / 60.0
    total_hours += hours
    print(f"Task: '{t.title}' | Org: {t.organization.name} | Status: {t.status} | Est Hours: {hours}h")

print(f"Total calculated assigned hours: {total_hours}h")
print("=" * 80)
