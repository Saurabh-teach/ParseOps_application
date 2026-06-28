import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tasks.models import Task
from organizations.models import Organization, OrganizationMembership
from tasks.calculations import calculate_task_score, calculate_employee_score, calculate_fatigue_score, calculate_final_assignment_score

org = Organization.objects.get(id="a902b370-1fac-4fd6-bde9-b6fd4978566e")

# We want to see what employees are available
print("AVAILABLE EMPLOYEES:")
memberships = OrganizationMembership.objects.filter(
    organization=org,
    is_active=True
).select_related('user')

for mem in memberships:
    user = mem.user
    assigned_hours = user.get_assigned_hours()
    print(f" - {user.email} (Role: {mem.role}) | Active: {mem.is_active} | Assigned hours: {assigned_hours}h | Capacity OK?: {assigned_hours < 6.5}")

# Let's check the task
task = Task.objects.get(title="Auto-Assign Task for Global Teach")
print(f"\nTask details:")
print(f" - Title: {task.title}")
print(f" - Estimated Hours: {task.estimated_hours}h")

# Calculate scores for all active members for this task
print("\nFinal Match Scores for this Task:")
for mem in memberships:
    user = mem.user
    if user.get_assigned_hours() < 6.5:
        score = calculate_final_assignment_score(task, user)
        print(f" - {user.email} (Role: {mem.role}): Match Score = {score}")
    else:
        print(f" - {user.email} (Role: {mem.role}): OUT OF CAPACITY (hours: {user.get_assigned_hours()}h)")
