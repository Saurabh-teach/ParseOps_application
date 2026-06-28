import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from organizations.models import Organization, OrganizationMembership

User = get_user_model()

print("=" * 80)
print("DATABASE STATE DIAGNOSTIC")
print("=" * 80)

print("USERS:")
users = User.objects.all()
for u in users:
    print(f" - ID: {u.id} | Email: {u.email} | First Name: {u.first_name}")

print("\nORGANIZATIONS:")
orgs = Organization.objects.all()
for o in orgs:
    print(f" - ID: {o.id} | Name: {o.name} | Owner: {o.owner.email if o.owner else 'None'} | Public: {o.is_public} | Active: {o.is_active}")

print("\nMEMBERSHIPS:")
mems = OrganizationMembership.objects.all()
for m in mems:
    print(f" - Org: {m.organization.name} | User: {m.user.email} | Role: {m.role} | Active: {m.is_active}")
print("=" * 80)
