import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from organizations.models import Organization, OrganizationMembership
from tasks.models import Task
from tasks.calculations import (
    calculate_task_score,
    calculate_employee_score,
    calculate_fatigue_score,
    calculate_final_assignment_score
)

User = get_user_model()
org_id = "a902b370-1fac-4fd6-bde9-b6fd4978566e"
org = Organization.objects.get(id=org_id)

print("=" * 80)
print(f"EXPLAINING ASSIGNMENT FOR ORGANIZATION: {org.name}")
print("=" * 80)

# Create a temporary mock task matching the user's input
task = Task(
    organization=org,
    title="Auto-Assign Task for Global Teach",
    priority="high",
    risk="medium",
    impact=7,
    estimated_hours=3.0
)

task_score = calculate_task_score(task)
print(f"MOCK TASK DETAILS:")
print(f" - Title: {task.title}")
print(f" - Priority: {task.priority} (Mapped: 3.0)")
print(f" - Risk: {task.risk} (Mapped: 2.0)")
print(f" - Impact: {task.impact}")
print(f" - Estimated Hours: {task.estimated_hours}h")
print(f" -> Task Score: {task_score}")
print("-" * 80)

memberships = OrganizationMembership.objects.filter(
    organization=org,
    is_active=True
).select_related('user')

print("CANDIDATE SUITABILITY BREAKDOWN:")
for membership in memberships:
    user = membership.user
    emp_score = calculate_employee_score(user)
    fatigue = calculate_fatigue_score(user)
    final_score = calculate_final_assignment_score(task, user)
    
    print(f"\nUser: {user.email}")
    print(f" - Role: {membership.role}")
    print(f" - Past Performance field: {user.past_performance}")
    print(f" - Experience Score field: {user.experience_score}")
    print(f" - Default Efficiency score field: {user.efficiency_score}")
    print(f" - Default Availability score field: {user.availability_score}")
    print(f" - Assigned Active Hours: {user.get_assigned_hours()}h")
    print(f" - Dynamic Employee Score: {emp_score}")
    print(f" - Dynamic Fatigue Score: {fatigue}")
    print(f" -> Final Match Score: {final_score}")

print("=" * 80)
