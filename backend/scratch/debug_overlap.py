import os
import django
import sys
from datetime import datetime, timedelta, timezone as dt_timezone

# Set up Django environment
sys.path.append('c:\\Users\\saura\\ParseOps\\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tasks.models import Task
from users.models import User
from tasks.services.scheduler import SchedulerService
from tasks.services.calendar import to_org_tz

def debug_overlap():
    print("--- DEBUG OVERLAP DETECTION ---")
    # Get all active tasks that have planned schedules
    tasks = Task.objects.filter(
        planned_start__isnull=False,
        planned_end__isnull=False,
        is_deleted=False
    ).exclude(status='done')
    
    print(f"Total active scheduled tasks: {tasks.count()}")
    for t in tasks:
        local_start = to_org_tz(t.planned_start, t.organization)
        local_end = to_org_tz(t.planned_end, t.organization)
        print(f"Task ID: {t.id} | Title: {t.title}")
        print(f"  Assignee: {t.assignee.email if t.assignee else 'None'} (ID: {t.assignee_id})")
        print(f"  Planned Start: {t.planned_start} (Local: {local_start})")
        print(f"  Planned End:   {t.planned_end} (Local: {local_end})")
        print(f"  Status: {t.status} | Schedule Status: {t.schedule_status}")
        print(f"  Required Assignees: {t.required_assignees}")
        
        # Test _get_busy_slots for this assignee
        if t.assignee_id:
            now = datetime.now(dt_timezone.utc)
            range_start = now - timedelta(days=2)
            range_end = now + timedelta(days=5)
            busy = SchedulerService._get_busy_slots(t.assignee_id, range_start, range_end)
            print(f"  Busy slots returned for assignee between {range_start} and {range_end}:")
            for b_start, b_end in busy:
                print(f"    - {b_start} to {b_end}")
            
            # Test find_earliest_slot
            start_search = now
            planned_start_l, planned_end_l = SchedulerService.find_earliest_slot(
                assignee_id=t.assignee_id,
                estimated_hours=1.0,
                org=t.organization,
                start_search_from=start_search
            )
            print(f"  Find Earliest Slot (1.0h) starting from {start_search}:")
            print(f"    - Local: {planned_start_l} to {planned_end_l}")

if __name__ == '__main__':
    debug_overlap()
