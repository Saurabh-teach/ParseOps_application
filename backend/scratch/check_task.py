import os, sys, django
sys.path.insert(0, r'C:\Users\saura\ParseOps\backend')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from tasks.models import Task
from organizations.models import OrganizationMembership

TASK_ID = '182ed370-91c0-4bdc-a65e-3581552c8823'

try:
    t = Task.objects.get(id=TASK_ID)
    print(f"Title        : {t.title}")
    print(f"Org Name     : {t.organization.name}")
    print(f"Org ID       : {t.organization.id}")
    print(f"visibility   : {t.visibility_type}")
    print(f"sharing      : {t.sharing_option}")
    print(f"Status       : {t.status} | Priority: {t.priority}")
    print(f"Impact       : {t.impact} | Risk: {t.risk}")
    print(f"Created by   : {t.created_by.email if t.created_by else 'None'}")
    print(f"Assignees    : {[a.email for a in t.assignees.all()]}")
    print(f"Visible to   : {[u.email for u in t.visible_to.all()]}")
    print()
    print("--- Owners of this org ---")
    for m in OrganizationMembership.objects.filter(
        organization=t.organization, role='owner', is_active=True
    ):
        print(f"  {m.user.email}")
except Task.DoesNotExist:
    print(f"ERROR: Task {TASK_ID} NOT FOUND in database.")
