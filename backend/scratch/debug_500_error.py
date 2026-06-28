import django
import os
import sys
import traceback

sys.path.append('c:/Users/saura/ParseOps/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from tasks.views import OrgTaskListView
from organizations.models import Organization, OrganizationMembership

try:
    org = Organization.objects.get(slug="amar_teach")
    print("Found organization:", org.name)
except Organization.DoesNotExist:
    org = Organization.objects.first()
    print("Organization 'amar_teach' not found, using:", org.name if org else "None")

if not org:
    print("No organization found at all.")
    sys.exit(1)

membership = OrganizationMembership.objects.filter(organization=org, is_active=True).first()
if not membership:
    print("No active membership found in org.")
    sys.exit(1)

user = membership.user
print("Authenticated user:", user.email)

factory = APIRequestFactory()
view = OrgTaskListView.as_view()
request = factory.get(f"/api/org/{org.slug}/tasks/")
force_authenticate(request, user=user)

print("\n--- Executing GET /api/org/tasks/ ---")
try:
    response = view(request, org_slug=org.slug)
    print("Status code:", response.status_code)
    if response.status_code >= 400:
        print("Response data:", response.data)
except Exception as e:
    print("\n--- ERROR CAUGHT ---")
    traceback.print_exc()
