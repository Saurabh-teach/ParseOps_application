import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tasks.models import Task
from django.contrib.auth import get_user_model
from tasks.services.scheduler import schedule_tasks_for_assignee
from django.db.models import Q

User = get_user_model()

print("Starting to fix broken tasks...")

tasks = Task.objects.filter(assignee__isnull=True, schedule_status='QUEUED', is_deleted=False)
fixed_count = 0

for task in tasks:
    print(f"Checking task: {task.title}")
    
    if 'Fill Task' in task.title:
        # Let's try to assign it to bhangalesaurabh20+mcm500@gmail.com
        user = User.objects.filter(email='bhangalesaurabh20+mcm500@gmail.com').first()
        if not user:
            user = task.created_by or getattr(task.goal, 'owner', None)
        if not user:
            user = User.objects.first()
            
        if user:
            task.assignee = user
            task.save(update_fields=['assignee'])
            print(f"Assigned {task.title} to {user.email}")
            schedule_tasks_for_assignee(assignee_id=user.id, org_id=task.organization.id)
            fixed_count += 1

print(f"Fixed {fixed_count} tasks!")
