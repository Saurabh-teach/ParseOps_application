import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tasks.models import Task
from organizations.models import Organization
from tasks.scheduler import run_scheduling, get_available_employees, rank_employees_for_task

org = Organization.objects.get(id="a902b370-1fac-4fd6-bde9-b6fd4978566e")
task = Task.objects.filter(organization=org, title="Frontend Auto-Scheduling Test").first()

if not task:
    print("Task 'Frontend Auto-Scheduling Test' not found!")
    sys.exit(1)

print("=" * 80)
print(f"DIAGNOSING TASK: '{task.title}'")
print(f" - ID: {task.id}")
print(f" - Organization: {task.organization.name}")
print(f" - Estimated Hours: {task.estimated_hours}h")
print(f" - Estimated Minutes: {task.estimated_minutes}m")
print(f" - Assignees: {[u.email for u in task.assignees.all()]}")
print(f" - Status: {task.status}")
print("-" * 80)

# Check available employees
avail = get_available_employees(org)
print(f"Available employees with capacity (< 6.5 hours): {[u.email for u in avail]}")
for u in avail:
    print(f" - {u.email}: assigned hours = {u.get_assigned_hours()}h")
print("-" * 80)

# Run scheduling for this task manually
print("Running scheduling manually for this task:")
ranked = rank_employees_for_task(task, avail)
for u, score in ranked:
    print(f" - Candidate: {u.email} | Match Score: {score}")

if ranked:
    print(f"Top candidate: {ranked[0][0].email}")
else:
    print("No candidates available!")
print("=" * 80)
