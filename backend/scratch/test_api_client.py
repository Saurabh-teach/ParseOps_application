import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from organizations.models import Organization
from django.urls import reverse

User = get_user_model()
user = User.objects.get(email="bhangalesaurabh20+owner@gmail.com")
org = Organization.objects.get(id="a902b370-1fac-4fd6-bde9-b6fd4978566e")

client = Client()
client.force_login(user)

url = "/api/tasks/create/"
payload = {
    "organization": str(org.id),
    "title": "Django Client Auto-Scheduling Test",
    "description": "Verifying API creation auto scheduling via test client",
    "priority": "high",
    "risk": "medium",
    "impact": 7,
    "estimated_hours": 3.0,
    "assignees": []
}

print("=" * 80)
print("MAKING POST REQUEST TO CREATE TASK:")
print("=" * 80)
response = client.post(url, data=payload, content_type="application/json")
print("STATUS CODE:", response.status_code)
print("RESPONSE DATA:")
import json
try:
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(response.content)
print("=" * 80)
