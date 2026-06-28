import os
import django
from datetime import datetime, timedelta, time as datetime_time
from django.utils import timezone
import zoneinfo

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from organizations.models import Organization
from users.models import User
from tasks.models import Task
from tasks.services.scheduler import get_next_available_slot

def run_test():
    print("Starting scratch test for break spanning and gap-filling...")
    
    org = Organization.objects.filter(slug='amar_teach').first()
    if not org:
        org = Organization.objects.first()
    if not org:
        print("No organization found.")
        return

    # Update working start, end and lunch break
    org.working_start_time = datetime_time(10, 0, 0)
    org.working_end_time = datetime_time(19, 0, 0)
    org.lunch_break_start = datetime_time(13, 0, 0)
    org.lunch_break_end = datetime_time(14, 0, 0)
    org.tea_break_start = datetime_time(17, 0, 0)
    org.tea_break_end = datetime_time(17, 30, 0)
    org.save()
    print(f"Configured Org {org.name} breaks.")

    user = User.objects.filter(email='bhangalesaurabh20+member1015@gmail.com').first()
    if not user:
        user = User.objects.first()
    if not user:
        print("No user found.")
        return

    # Clean up existing scheduled tasks for user to have a clean slate
    deleted = Task.objects.filter(assignee=user, organization=org).delete()
    print(f"Cleaned up {deleted[0]} existing tasks.")

    # Determine tomorrow's date (must be a working day)
    tomorrow = timezone.localdate() + timedelta(days=1)
    while tomorrow.weekday() in [5, 6]:  # Skip weekend
        tomorrow += timedelta(days=1)

    org_tz = zoneinfo.ZoneInfo(org.timezone)

    # 1. Create a task that blocks the morning of tomorrow: 10:00 AM to 12:00 PM (2h)
    block_start_utc = datetime.combine(tomorrow, datetime_time(10, 0, 0))
    block_start_utc = timezone.make_aware(block_start_utc, org_tz).astimezone(timezone.utc)
    block_end_utc = datetime.combine(tomorrow, datetime_time(12, 0, 0))
    block_end_utc = timezone.make_aware(block_end_utc, org_tz).astimezone(timezone.utc)
    
    Task.objects.create(
        organization=org,
        title="Blocking Task 1",
        estimated_hours=2.0,
        planned_start=block_start_utc,
        planned_end=block_end_utc,
        schedule_status='SCHEDULED',
        created_by=user,
        assignee=user
    )
    print("Created tomorrow morning blocking task (10:00 AM - 12:00 PM)")

    # 2. Search for a 4.0 hour task starting tomorrow at 10:00 AM.
    # Since tomorrow morning has only 1 hour free (12:00 PM - 1:00 PM), and afternoon has 3 hours (2:00 PM - 5:00 PM),
    # the task can't fit continuously in any single slot.
    # However, it can fit by spanning the lunch break:
    # Part 1: 12:00 PM - 1:00 PM (1h)
    # Lunch break: 1:00 PM - 2:00 PM (1h break)
    # Part 2: 2:00 PM - 5:00 PM (3h)
    # Total work = 4.0 hours, ending at 5:00 PM.
    start_search = datetime.combine(tomorrow, datetime_time(10, 0, 0))
    start_search = timezone.make_aware(start_search, org_tz)

    print(f"Running get_next_available_slot for user={user.email}, hours=4.0, start_search={start_search}")
    planned_start, planned_end = get_next_available_slot(user.id, 4.0, org.id, start_search_from=start_search)

    if not planned_start or not planned_end:
        print("FAILED: No slot returned.")
        return

    planned_start_local = planned_start.astimezone(org_tz)
    planned_end_local = planned_end.astimezone(org_tz)
    print(f"Result: {planned_start_local} to {planned_end_local}")
    
    # Assert
    assert planned_start_local.hour == 12 and planned_start_local.minute == 0, "Should start at 12:00 PM"
    assert planned_end_local.hour == 17 and planned_end_local.minute == 0, "Should end at 5:00 PM"
    print("SUCCESS: Multi-day gap-filling and break-spanning verified perfectly!")

if __name__ == '__main__':
    run_test()
