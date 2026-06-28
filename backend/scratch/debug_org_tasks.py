import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from organizations.models import Organization, OrganizationMembership
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

print("=" * 80)
org_slug = "amar_teach"
try:
    org = Organization.objects.get(slug=org_slug)
    print(f"Found Organization '{org_slug}': ID = {org.id}")
except Organization.DoesNotExist:
    print(f"Organization '{org_slug}' does not exist.")
    sys.exit(1)

memberships = OrganizationMembership.objects.filter(organization=org)
member = memberships.filter(is_active=True).first()
user = member.user
print(f"Simulating requests as: {user.email}")

# Generate JWT Token
refresh = RefreshToken.for_user(user)
access_token = str(refresh.access_token)
headers = {
    "HTTP_AUTHORIZATION": f"Bearer {access_token}"
}

client = Client(HTTP_HOST="127.0.0.1")

# Test POST request with exact frontend payload
print("\nPOST /api/org/amar_teach/tasks/ (Full Frontend Payload)")
payload = {
    "title": "Debug Frontend Task",
    "description": "",
    "issue_type": "task",
    "priority": "medium",
    "status": "todo",
    "assignees": [str(user.id)],
    "watchers": [],
    "visible_to": [],
    "sharing_option": "specific",
    "shared_viewers": [],
    "required_assignees": 1,
    "impact": 5,
    "risk": "medium",
    "reminder_preference": "none",
    "estimated_minutes": 60,
    "estimated_hours": 1.0
}
res_post = client.post(f"/api/org/{org_slug}/tasks/", data=payload, content_type="application/json", **headers)
print("Status Code:", res_post.status_code)
try:
    print("Response JSON:", res_post.json())
except Exception as e:
    print("Error parsing response:", e, res_post.content[:500])

print("=" * 80)
