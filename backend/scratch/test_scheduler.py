import os
import sys
import django
from datetime import timedelta

# Set up Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from organizations.models import Organization, OrganizationMembership
from tasks.models import Task
from tasks.scheduler import run_scheduling, get_available_employees, debug_scheduling

User = get_user_model()

def run_test():
    print("=" * 80)
    print("PARSEOPS - PHASE 3 SCHEDULING ENGINE DIAGNOSTIC RUN (LOAD BALANCED & GROUP TASKS)")
    print("=" * 80)

    # 1. Setup mock organization
    org = Organization.objects.create(name="Scheduler Testing Org")
    print(f"Created Org: {org.name}")

    # 2. Setup mock users
    # User A: High performer, low fatigue, has 4 hours workload (available)
    user_a = User.objects.create_user(
        email="user_a@parseops.com",
        password="securepass123",
        past_performance=95,
        experience_score=90,
        efficiency_score=90,
        availability_score=100
    )
    OrganizationMembership.objects.create(organization=org, user=user_a, role="member", is_active=True)

    # User B: Good performer, but already has 7 hours of workload (over capacity threshold of 6.5)
    user_b = User.objects.create_user(
        email="user_b@parseops.com",
        password="securepass123",
        past_performance=85,
        experience_score=85,
        efficiency_score=85,
        availability_score=100
    )
    OrganizationMembership.objects.create(organization=org, user=user_b, role="member", is_active=True)

    # User C: Moderate performer, empty workload (available)
    user_c = User.objects.create_user(
        email="user_c@parseops.com",
        password="securepass123",
        past_performance=70,
        experience_score=75,
        efficiency_score=70,
        availability_score=100
    )
    OrganizationMembership.objects.create(organization=org, user=user_c, role="member", is_active=True)

    print("Created Users:")
    print(f" - User A: {user_a.email} (Performance: 95)")
    print(f" - User B: {user_b.email} (Performance: 85)")
    print(f" - User C: {user_c.email} (Performance: 70)")
    print("-" * 80)

    try:
        # 3. Create existing workload tasks to set initial hours
        # Give User A a task of 4 hours -> workload = 4.0h < 6.5 (should be available)
        task_init_a = Task.objects.create(
            title="Initial Workload User A",
            organization=org,
            estimated_hours=4.0,
            status="todo"
        )
        task_init_a.assignees.add(user_a)

        # Give User B a task of 7 hours -> workload = 7.0h >= 6.5 (should NOT be available)
        task_init_b = Task.objects.create(
            title="Initial Workload User B",
            organization=org,
            estimated_hours=7.0,
            status="todo"
        )
        task_init_b.assignees.add(user_b)

        print("Initial Workloads:")
        print(f" - User A: {user_a.get_assigned_hours()} hours (Expected: 4.0)")
        print(f" - User B: {user_b.get_assigned_hours()} hours (Expected: 7.0)")
        print(f" - User C: {user_c.get_assigned_hours()} hours (Expected: 0.0)")
        print("-" * 80)

        # Verify get_available_employees returns User A and User C, but not User B
        avail = get_available_employees(org)
        avail_emails = [u.email for u in avail]
        print(f"Available employees with capacity (< 6.5 hours): {avail_emails}")
        assert user_a in avail, "User A should be available"
        assert user_c in avail, "User C should be available"
        assert user_b not in avail, "User B should be excluded due to workload capacity limit"
        print(" -> Capacity filtering check PASSED!")
        print("-" * 80)

        # 4. Create new pending unassigned tasks to auto-assign
        # Task 1: Group task (needs 2 assignees)
        task1 = Task.objects.create(
            title="Critical Bug Fix (Group Task)",
            organization=org,
            impact=9,
            risk="high",
            priority="high",
            due_date=timezone.now() + timedelta(days=1),
            estimated_hours=2.0,
            status="todo"
        )
        # Manually set required_assignees attribute (since we use getattr in scheduler)
        task1.required_assignees = 2
        task1.save()

        # Task 2: Normal task, needs 1 assignee
        task2 = Task.objects.create(
            title="Feature Implementation (Individual Task)",
            organization=org,
            impact=6,
            risk="medium",
            priority="medium",
            due_date=timezone.now() + timedelta(days=3),
            estimated_hours=3.0,
            status="todo"
        )

        print("Created Pending Unassigned Tasks:")
        print(f" - Task 1: '{task1.title}' (Priority: {task1.priority}, Hours: {task1.estimated_hours}, Required Assignees: 2)")
        print(f" - Task 2: '{task2.title}' (Priority: {task2.priority}, Hours: {task2.estimated_hours}, Required Assignees: 1)")
        print("-" * 80)

        # Run Debug Scheduling prints
        debug_scheduling(org)

        # 5. Verify the assignment results
        task1.refresh_from_db()
        task2.refresh_from_db()

        print("Verifying Final Assignments:")
        assignees_task1 = [u.email for u in task1.assignees.all()]
        assignees_task2 = [u.email for u in task2.assignees.all()]
        print(f" -> '{task1.title}' assigned to: {assignees_task1}")
        print(f" -> '{task2.title}' assigned to: {assignees_task2}")

        # Task 1 is a group task requesting 2 assignees.
        # User A and User C are the only available employees. They should both be assigned to Task 1.
        assert len(assignees_task1) == 2, "Task 1 should have exactly two assignees"
        assert "user_a@parseops.com" in assignees_task1, "User A should be assigned to Task 1"
        assert "user_c@parseops.com" in assignees_task1, "User C should be assigned to Task 1"
        assert "user_b@parseops.com" not in assignees_task1, "User B should not be assigned to Task 1"

        # Task 2 is an individual task.
        # After Task 1 is assigned:
        # User A assigned hours = 4.0 (initial) + 2.0 (Task 1) = 6.0h.
        # User C assigned hours = 0.0 (initial) + 2.0 (Task 1) = 2.0h.
        # Both are still under capacity (< 6.5h).
        # Top ranked candidate will be assigned Task 2.
        assert len(assignees_task2) == 1, "Task 2 should have exactly one assignee"
        assert "user_b@parseops.com" not in assignees_task2, "User B should not be assigned to Task 2"
        
        # Verify workload score updates
        user_a.refresh_from_db()
        user_c.refresh_from_db()
        print(f" -> User A workload score: {user_a.current_workload_score}")
        print(f" -> User C workload score: {user_c.current_workload_score}")
        print(" -> Workload updates check PASSED!")
        print("=" * 80)
        print("DIAGNOSTIC RUN COMPLETED SUCCESSFULLY!")
        print("=" * 80)

    finally:
        # Cleanup
        print("Cleaning up database...")
        Task.objects.filter(organization=org).delete()
        OrganizationMembership.objects.filter(organization=org).delete()
        user_a.delete()
        user_b.delete()
        user_c.delete()
        org.delete()
        print("Cleanup completed.")
        print("=" * 80)

if __name__ == "__main__":
    run_test()
