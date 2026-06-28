import django
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

# Set up Django
sys.path.append('c:/Users/saura/ParseOps/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from tasks.views import OrgTaskListView
from organizations.models import Organization, OrganizationMembership
from tasks.models import Task

User = get_user_model()

# Setup test user and organization
org = Organization.objects.first()
if not org:
    org = Organization.objects.create(name="Verification Org", slug="verification-org")

# Let's find an active user in the organization to make the request
membership = OrganizationMembership.objects.filter(organization=org, is_active=True).first()
if membership:
    user = membership.user
else:
    user = User.objects.first()
    if not user:
        user = User.objects.create_user(email="test_verifier@parseops.com", password="securepass123")
    OrganizationMembership.objects.create(organization=org, user=user, role="owner", is_active=True)

# Make sure we have at least one other active member to assign to
memberships = OrganizationMembership.objects.filter(organization=org, is_active=True)
print(f"Active members in org '{org.name}': {[m.user.email for m in memberships]}")

# Setup factory
factory = APIRequestFactory()
view = OrgTaskListView.as_view()

# Prepare task data: Empty assignees, Required Assignees = 1
data = {
    "title": "API Verification Task 1",
    "description": "Checking backend scheduling trigger from OrgTaskListView",
    "priority": "high",
    "estimated_hours": 2.0,
    "required_assignees": 1,
    "assignees": []
}

# Create request
request = factory.post(f"/api/org/{org.slug}/tasks/", data, format='json')
force_authenticate(request, user=user)

print("\n--- Executing OrgTaskListView Post ---")
response = view(request, org_slug=org.slug)

print("Response status code:", response.status_code)
print("Response data:", response.data)

if response.status_code == 201:
    task_id = response.data['id']
    task = Task.objects.get(id=task_id)
    assignee_emails = [u.email for u in task.assignees.all()]
    print(f"\nCreated Task: '{task.title}'")
    print(f"Assignees: {assignee_emails}")
    if assignee_emails:
        print("\n>>> SUCCESS: Auto-scheduling worked fine on task creation! <<<")
    else:
        print("\n>>> WARNING: Task created but no assignees assigned (check workload capacity or availability). <<<")
else:
    print("\n>>> FAILED to create task via view <<<")
