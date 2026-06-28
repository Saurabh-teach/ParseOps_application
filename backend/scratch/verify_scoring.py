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
from organizations.models import Organization
from tasks.models import Task
from users.models import LeaveRequest
from tasks.calculations import (
    calculate_task_score,
    calculate_employee_score,
    calculate_fatigue_score,
    calculate_final_assignment_score
)

User = get_user_model()

def run_diagnostic():
    print("=" * 60)
    print("PARSEOPS - PHASE 2 SCORING SYSTEM DIAGNOSTIC RUN")
    print("=" * 60)
    
    # 1. Setup mock organization and user
    org = Organization.objects.create(name="Diagnostic Org")
    user = User.objects.create_user(
        email="diagnostic.employee@parseops.com",
        password="securepass123",
        past_performance=85,
        experience_score=90,
        efficiency_score=80,
        availability_score=100,
        current_workload_score=0
    )
    
    print(f"Created Org: {org.name}")
    print(f"Created User: {user.email}")
    print(f" - Performance: {user.past_performance}")
    print(f" - Experience: {user.experience_score}")
    print(f" - Efficiency: {user.get_efficiency()}")
    print(f" - Availability: {user.get_availability()}")
    print("-" * 60)
    
    try:
        # 2. Test Task Scoring
        # Task 1: High priority, high impact, moderate risk, due in 3 days, 16 effort hours
        due_date = timezone.now() + timedelta(days=3)
        task1 = Task.objects.create(
            title="High Impact Feature Development",
            organization=org,
            impact=9,
            risk=4,
            priority="high",
            due_date=due_date,
            estimated_hours=16.0
        )
        task1_score = calculate_task_score(task1)
        print("TASK 1 SCORING:")
        print(f" - Title: '{task1.title}'")
        print(f" - Priority: {task1.priority} (mapped value: 3.0)")
        print(f" - Impact: {task1.impact}, Risk: {task1.risk}")
        print(f" - Due: in 3 days (urgency: {1.0 / (3.0 + 1.0) = :.4f})")
        print(f" - Effort: {task1.estimated_hours} hours")
        print(f" -> CALCULATED TASK SCORE: {task1_score}")
        print("-" * 60)

        # 3. Test Employee Scoring & Fatigue before assignments
        emp_score_before = calculate_employee_score(user)
        fatigue_before = calculate_fatigue_score(user)
        match_score_before = calculate_final_assignment_score(task1, user)
        print("EMPLOYEE INITIAL SUITABILITY:")
        print(f" -> EMPLOYEE SCORE: {emp_score_before}")
        print(f" -> FATIGUE SCORE: {fatigue_before}")
        print(f" -> FINAL MATCH SCORE (TASK 1): {match_score_before}")
        print("-" * 60)

        # 4. Assign task and test changes
        task1.assignees.add(user)
        emp_score_after = calculate_employee_score(user)
        fatigue_after = calculate_fatigue_score(user)
        match_score_after = calculate_final_assignment_score(task1, user)
        print("EMPLOYEE SUITABILITY AFTER 16-HOUR TASK ASSIGNMENT:")
        print(f" - Assigned Hours: {user.get_assigned_hours()} hours")
        print(f" -> EMPLOYEE SCORE (with workload): {emp_score_after}")
        print(f" -> FATIGUE SCORE: {fatigue_after}")
        print(f" -> FINAL MATCH SCORE (TASK 1): {match_score_after}")
        print("-" * 60)

        # 5. Place user on leave and test availability impact
        today = timezone.localdate()
        leave = LeaveRequest.objects.create(
            user=user,
            organization=org,
            leave_type="Sick",
            start_date=today,
            end_date=today,
            status="Approved"
        )
        emp_score_leave = calculate_employee_score(user)
        match_score_leave = calculate_final_assignment_score(task1, user)
        print("EMPLOYEE SUITABILITY AFTER APPROVED LEAVE:")
        print(f" - On Approved Leave Today: {user.get_availability() == 0.0}")
        print(f" -> EMPLOYEE SCORE: {emp_score_leave}")
        print(f" -> FINAL MATCH SCORE (TASK 1): {match_score_leave}")
        print("-" * 60)

    finally:
        # Cleanup
        print("Cleaning up database...")
        Task.objects.filter(organization=org).delete()
        LeaveRequest.objects.filter(organization=org).delete()
        user.delete()
        org.delete()
        print("Cleanup completed.")
        print("=" * 60)

if __name__ == "__main__":
    run_diagnostic()
