import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tasks.models import Task
from organizations.models import Organization, OrganizationMembership
from tasks.scheduler import run_scheduling, get_available_employees, rank_employees_for_task
from django.db import transaction

org = Organization.objects.get(id="a902b370-1fac-4fd6-bde9-b6fd4978566e")

# We run inside a transaction that is rolled back at the end
with transaction.atomic():
    # 1. Reset assignees for the test task
    task = Task.objects.get(title="Auto-Assign Task for Global Teach")
    task.assignees.clear()
    print(f"Cleared assignees for task: '{task.title}'")
    
    # 2. Run simulation
    print("\nSimulating run_scheduling():")
    pending_tasks = Task.objects.filter(
        organization=org,
        is_deleted=False
    ).exclude(status='done').filter(assignees__isnull=True)
    
    print(f"Unassigned pending tasks count: {pending_tasks.count()}")
    for t in pending_tasks:
        print(f" - Title: '{t.title}' | Score: {t.calculate_score()} | Est Hours: {t.estimated_hours}h")
        
    # Run the scheduler
    assignments = run_scheduling(org)
    print("\nResulting assignments:")
    for t, emp, score in assignments:
        print(f" -> Assigned task '{t.title}' to '{emp.email}' with Final Match Score: {score}")

    # Roll back transaction so database is not modified
    transaction.set_rollback(True)
