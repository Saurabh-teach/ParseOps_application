import re

with open('c:/Users/saura/ParseOps/backend/tasks/services.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """class TaskService:"""

replacement = """import math
from datetime import timedelta
from django.utils import timezone

PRODUCTIVE_MINUTES_PER_DAY = int(6.5 * 60) # 390 minutes

def add_business_days(start_date, days_to_add):
    current_date = start_date
    # Ensure current_date is not on a weekend to start with
    while current_date.weekday() >= 5:
        current_date += timedelta(days=1)
        
    while days_to_add > 0:
        current_date += timedelta(days=1)
        if current_date.weekday() < 5: # Monday-Friday
            days_to_add -= 1
    return current_date

class TaskService:
    @staticmethod
    def calculate_ideal_due_date(organization_id, assignees, estimated_minutes, exclude_task_id=None):
        if not estimated_minutes:
            return None
            
        start_from = timezone.now()
        max_days_added = 0
        
        # If no assignees, just calculate based on standalone time
        if not assignees:
            days_needed = math.ceil(estimated_minutes / PRODUCTIVE_MINUTES_PER_DAY)
            days_to_add = max(0, days_needed - 1)
            return add_business_days(start_from, days_to_add).replace(hour=18, minute=0, second=0, microsecond=0)
            
        for user_id in assignees:
            # Calculate backlog for this specific user
            pending_tasks = Task.objects.filter(
                organization_id=organization_id,
                assignees__id=user_id,
                status__in=['backlog', 'todo', 'in_progress', 'in_review', 'testing'],
                is_deleted=False
            )
            if exclude_task_id:
                pending_tasks = pending_tasks.exclude(id=exclude_task_id)
                
            backlog_minutes = sum([t.estimated_minutes for t in pending_tasks if t.estimated_minutes])
            total_minutes = backlog_minutes + estimated_minutes
            
            days_needed = math.ceil(total_minutes / PRODUCTIVE_MINUTES_PER_DAY)
            days_to_add = max(0, days_needed - 1)
            
            if days_to_add > max_days_added:
                max_days_added = days_to_add
                
        calculated_date = add_business_days(start_from, max_days_added)
        # End of the work day
        calculated_date = calculated_date.replace(hour=18, minute=0, second=0, microsecond=0)
        return calculated_date
"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/backend/tasks/services.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("tasks/services.py patched")
