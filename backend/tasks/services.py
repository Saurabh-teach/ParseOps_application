from tasks.models import Task
from notifications.models import Notification
from notifications.webpush import send_web_push


import math
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

def add_business_days_for_user(start_date, days_to_add, user_id):
    current_date = start_date
    # Ensure starting date is a business day and they are not on leave
    while True:
        if current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue
        from users.models import LeaveRequest
        is_on_leave = LeaveRequest.objects.filter(
            user_id=user_id,
            status='Approved',
            start_date__lte=current_date.date() if hasattr(current_date, 'date') else current_date,
            end_date__gte=current_date.date() if hasattr(current_date, 'date') else current_date
        ).exists()
        if is_on_leave:
            current_date += timedelta(days=1)
            continue
        break
        
    while days_to_add > 0:
        current_date += timedelta(days=1)
        if current_date.weekday() >= 5: # Skip weekend
            continue
        from users.models import LeaveRequest
        is_on_leave = LeaveRequest.objects.filter(
            user_id=user_id,
            status='Approved',
            start_date__lte=current_date.date() if hasattr(current_date, 'date') else current_date,
            end_date__gte=current_date.date() if hasattr(current_date, 'date') else current_date
        ).exists()
        if is_on_leave: # Skip leave day
            continue
        days_to_add -= 1
    return current_date

def get_user_productive_minutes(user_id=None, organization=None):
    from django.utils import timezone
    from datetime import timedelta
    
    # We need an organization to accurately calculate timezones, default to 390 if missing
    if not organization:
        return 390
        
    day = timezone.now().date()
    # Find next working day, simple loop skipping weekends to get a base day
    while day.weekday() >= 5:
        day += timedelta(days=1)
        
    from tasks.services.calendar import get_working_intervals
    intervals = get_working_intervals(day, organization, user=user_id)
    mins = sum(int(round((end - start).total_seconds() / 60.0)) for start, end in intervals)
    
    # Fallback to standard if no intervals found
    return mins if mins > 0 else 390


class TaskService:
    @staticmethod
    def calculate_ideal_due_date(organization_id, assignees, estimated_minutes, exclude_task_id=None):
        if not estimated_minutes:
            return None
            
        start_from = timezone.now()
        
        from organizations.models import Organization
        org = Organization.objects.filter(id=organization_id).first()
        
        # If no assignees, just calculate based on standalone time
        if not assignees:
            prod_mins = get_user_productive_minutes(None, org)
            days_needed = math.ceil(estimated_minutes / prod_mins)
            days_to_add = max(0, days_needed - 1)
            return add_business_days(start_from, days_to_add).replace(hour=18, minute=0, second=0, microsecond=0)
            
        max_calculated_date = None
        for user_id in assignees:
            # Calculate backlog for this specific user
            pending_tasks = Task.objects.filter(
                organization_id=organization_id,
                assignee_id=user_id,
                status__in=['backlog', 'todo', 'in_progress', 'in_review', 'testing'],
                is_deleted=False
            )
            if exclude_task_id:
                pending_tasks = pending_tasks.exclude(id=exclude_task_id)
                
            backlog_minutes = sum([t.estimated_minutes for t in pending_tasks if t.estimated_minutes])
            total_minutes = backlog_minutes + estimated_minutes
            
            prod_mins = get_user_productive_minutes(user_id, org)
            days_needed = math.ceil(total_minutes / prod_mins)
            days_to_add = max(0, days_needed - 1)
            
            user_date = add_business_days_for_user(start_from, days_to_add, user_id)
            if not max_calculated_date or user_date > max_calculated_date:
                max_calculated_date = user_date
                
        # End of the work day
        if max_calculated_date:
            max_calculated_date = max_calculated_date.replace(hour=18, minute=0, second=0, microsecond=0)
        return max_calculated_date

    @staticmethod
    def update_task_status(task, status):
        task.status = status
        task.save()
        return task

    @staticmethod
    def soft_delete_task(task):
        task.soft_delete()
        return True


class NotificationService:
    @staticmethod
    def send_notification(recipient, n_type, title, message, link=None, organization=None):
        data = {}
        if link:
            data['link'] = link
            
       
        notification = Notification.objects.create(
            user=recipient,
            notification_type=n_type,
            title=title,
            message=message,
            organization=organization,
            data=data
        )
        
        
        try:
            send_web_push(
                user=recipient,
                title=title,
                body=message,
                link=link
            )
        except Exception as e:
            print("Failed to send web push:", e)
            
        return notification
