import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tasks.models import Task
from organizations.models import Organization

org = Organization.objects.get(id="a902b370-1fac-4fd6-bde9-b6fd4978566e")
tasks = Task.objects.filter(organization=org).order_by('-created_at')

print("=" * 80)
print(f"ALL TASKS IN ORGANIZATION: {org.name}")
print("=" * 80)
for t in tasks:
    assignees = [u.email for u in t.assignees.all()]
    print(f"Task: '{t.title}' | Status: {t.status} | Created By: {t.created_by.email if t.created_by else 'None'} | Assignees: {assignees}")
print("=" * 80)
