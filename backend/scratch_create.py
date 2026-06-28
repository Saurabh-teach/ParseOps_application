import os
import django
import sys

sys.path.append(r"c:\Users\saura\ParseOps\backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from tasks.models import Task
from users.models import CustomUser
from organizations.models import Organization
from rest_framework.test import APIClient

org = Organization.objects.first()
user = CustomUser.objects.first()

client = APIClient()
client.force_authenticate(user=user)

url = f"/api/organizations/{org.slug}/tasks/"

data = {
    "title": "Debug Task " + str(django.utils.timezone.now().timestamp()),
    "description": "test",
    "issue_type": "task",
    "priority": "medium",
    "status": "todo",
    "estimated_hours": 1.0,
    "assignees": [str(user.id)]
}

with open("output.txt", "w") as f:
    try:
        response = client.post(url, data, format='json')
        f.write(f"STATUS: {response.status_code}\n")
        f.write(f"RESPONSE: {response.data}\n")
    except Exception as e:
        import traceback
        f.write("ERROR!\n")
        f.write(traceback.format_exc())
