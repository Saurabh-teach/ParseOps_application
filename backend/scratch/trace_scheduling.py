import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tasks.models import Task
from organizations.models import Organization
from django.db.models import Q

org = Organization.objects.get(id="a902b370-1fac-4fd6-bde9-b6fd4978566e")

print("=" * 80)
print(f"DETAILED TASK DETAILS FOR ORG: {org.name}")
print("=" * 80)

tasks = Task.objects.filter(organization=org).order_by('-created_at')
for t in tasks:
    assignees = [u.email for u in t.assignees.all()]
    print(f"Task: '{t.title}'")
    print(f" - Status: {t.status}")
    print(f" - Estimated Hours: {t.estimated_hours}h")
    print(f" - Estimated Minutes: {t.estimated_minutes}m")
    print(f" - Assignees: {assignees}")
    print(f" - Created At: {t.created_at}")
    print("-" * 50)

print("=" * 80)
