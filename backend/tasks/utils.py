from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q

# Break-aware planning constants
STANDARD_WORKDAY_HOURS = 8.5
LUNCH_BREAK_HOURS = 1.0
TEA_BREAK_HOURS = 1.0
# Fallback effective focused work per day = 8.5 - 1.0 - 1.0 = 6.5 hours
EFFECTIVE_WORK_HOURS = STANDARD_WORKDAY_HOURS - LUNCH_BREAK_HOURS - TEA_BREAK_HOURS

def get_user_effective_work_hours(user=None, organization=None):
    if not user or not organization:
        return EFFECTIVE_WORK_HOURS
    from tasks.services.calendar import get_working_intervals
    from django.utils import timezone
    from datetime import timedelta
    
    # Use a dummy workday to calculate typical capacity
    dummy_day = timezone.now().date()
    while dummy_day.weekday() >= 5:
        dummy_day -= timedelta(days=1)
        
    intervals = get_working_intervals(dummy_day, organization, user=user)
    total_seconds = sum((end - start).total_seconds() for start, end in intervals)
    if total_seconds > 0:
        return total_seconds / 3600.0
    return EFFECTIVE_WORK_HOURS

def count_workdays(start_date, end_date):
    """
    Counts number of weekdays (Monday to Friday) between start_date and end_date (inclusive).
    """
    if start_date > end_date:
        return 0
    days = (end_date - start_date).days + 1
    workdays = 0
    for i in range(days):
        d = start_date + timedelta(days=i)
        if d.weekday() < 5:  # 0 = Monday, 4 = Friday
            workdays += 1
    return workdays

def get_task_daily_load(task, target_date):
    """
    Calculates the daily workload (in hours) of a task on a specific target_date.
    If the task is completed or soft-deleted, it has 0 load.
    """
    if task.status == 'done' or task.is_deleted:
        return 0.0

    # If the task is SCHEDULED, calculate load based on planned start and end
    if task.schedule_status == 'SCHEDULED' and task.planned_start and task.planned_end:
        from django.utils import timezone
        p_start = timezone.localtime(task.planned_start) if timezone.is_aware(task.planned_start) else task.planned_start
        p_end = timezone.localtime(task.planned_end) if timezone.is_aware(task.planned_end) else task.planned_end
        
        start_date = p_start.date()
        end_date = p_end.date()
        
        if target_date < start_date or target_date > end_date:
            return 0.0
            
        if start_date == end_date:
            total_duration = (p_end - p_start).total_seconds() / 3600.0
            # Exclude breaks if they overlap
            if p_start.hour < 13 and p_end.hour >= 14:
                total_duration -= 1.0
            if p_start.hour < 17 and (p_end.hour > 17 or (p_end.hour == 17 and p_end.minute >= 30)):
                total_duration -= 0.5
            return max(0.0, total_duration)
        else:
            # Multi-day span calculation
            if target_date == start_date:
                end_of_day = p_start.replace(hour=18, minute=0, second=0, microsecond=0)
                duration = (end_of_day - p_start).total_seconds() / 3600.0
                if p_start.hour < 13:
                    duration -= 1.0
                if p_start.hour < 17:
                    duration -= 0.5
                return max(0.0, duration)
            elif target_date == end_date:
                start_of_day = p_end.replace(hour=9, minute=0, second=0, microsecond=0)
                duration = (p_end - start_of_day).total_seconds() / 3600.0
                if p_end.hour >= 14:
                    duration -= 1.0
                if p_end.hour > 17 or (p_end.hour == 17 and p_end.minute >= 30):
                    duration -= 0.5
                return max(0.0, duration)
            else:
                return 7.5

    # Determine start date
    start = task.start_date
    if not start:
        start = task.created_at.date() if task.created_at else timezone.now().date()

    # Determine due date (due_date is a DateTimeField now, so we take its date part)
    due = task.due_date.date() if task.due_date else None

    # If target date is before start date or after due date, load is 0
    if target_date < start:
        return 0.0
    if due and target_date > due:
        return 0.0

    # Retrieve total estimated hours
    total_hours = task.total_estimated_minutes / 60.0

    if total_hours <= 0.0:
        return 0.0

    # If there is no due date, we assume the load is concentrated on the start date
    if not due:
        return total_hours if start == target_date else 0.0

    # Count workdays between start and due
    workday_cnt = count_workdays(start, due)
    if workday_cnt == 0:
        return 0.0

    return total_hours / workday_cnt

def get_user_daily_load(user_id, date, organization_id=None, exclude_task_id=None):
    """
    Computes the total task workload (in hours) assigned to a user on a given date.
    """
    from tasks.models import Task
    tasks = Task.objects.filter(
        assignee_id=user_id,
        is_deleted=False
    ).exclude(status='done')

    if organization_id:
        tasks = tasks.filter(organization_id=organization_id)
    if exclude_task_id:
        tasks = tasks.exclude(id=exclude_task_id)

    total_load = 0.0
    for task in tasks.select_related('assignee'):
        total_load += get_task_daily_load(task, date)
    return total_load

def get_user_weekly_load(user_id, date, organization_id=None, exclude_task_id=None):
    """
    Computes the total task workload (in hours) assigned to a user during the week of the given date.
    """
    # Find Monday of that week
    monday = date - timedelta(days=date.weekday())
    weekly_hours = 0.0
    for i in range(5):  # Mon, Tue, Wed, Thu, Fri
        day = monday + timedelta(days=i)
        weekly_hours += get_user_daily_load(user_id, day, organization_id, exclude_task_id)
    return weekly_hours

def calculate_days_needed(estimated_hours):
    """
    Calculates the number of days needed to complete the task based on effective daily focused hours.
    """
    if not estimated_hours:
        return 0.0
    return float(estimated_hours) / EFFECTIVE_WORK_HOURS

def suggest_realistic_due_date(start_date, estimated_hours, user_id=None, organization_id=None, exclude_task_id=None):
    """
    Suggests a realistic due date based on the estimated hours, weekends, and optionally the user's workload.
    Returns a timezone-aware datetime set to 5:00 PM of the suggested day.
    """
    if not start_date:
        start_date = timezone.now().date()
    elif isinstance(start_date, datetime):
        start_date = start_date.date()

    remaining_hours = float(estimated_hours or 0.0)
    if remaining_hours <= 0.0:
        # Default to today if no estimation
        suggested_day = start_date
    else:
        current_day = start_date
        safety_counter = 0
        # Iterate day-by-day to allocate estimated hours based on remaining daily capacity
        while remaining_hours > 0.0 and safety_counter < 365:
            safety_counter += 1
            # Skip weekends
            if current_day.weekday() >= 5:
                current_day += timedelta(days=1)
                continue

            # Calculate user's capacity on this day
            if user_id:
                from users.models import LeaveRequest
                is_on_leave = LeaveRequest.objects.filter(
                    user_id=user_id,
                    status='Approved',
                    start_date__lte=current_day,
                    end_date__gte=current_day
                ).exists()
                if is_on_leave:
                    capacity = 0.0
                else:
                    load = get_user_daily_load(user_id, current_day, organization_id, exclude_task_id)
                    capacity = max(0.0, EFFECTIVE_WORK_HOURS - load)
            else:
                capacity = EFFECTIVE_WORK_HOURS

            # If capacity is 0, we can't work on this day, skip it
            if capacity <= 0.0:
                current_day += timedelta(days=1)
                continue

            work_done = min(remaining_hours, capacity)
            remaining_hours -= work_done

            if remaining_hours <= 0.0:
                suggested_day = current_day
                break

            current_day += timedelta(days=1)
        else:
            suggested_day = current_day

    # Return timezone-aware datetime representing 5:00 PM (17:00) on the suggested day
    local_dt = datetime.combine(suggested_day, datetime.min.time().replace(hour=17))
    return timezone.make_aware(local_dt, timezone.get_current_timezone())

def get_load_warnings(user_id, date, organization_id=None, exclude_task_id=None):
    """
    Returns warnings if the user is overloaded on the given date or within the week of the given date.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
        user_name = f"{user.first_name} {user.last_name}".strip() or user.email
    except User.DoesNotExist:
        user_name = "User"

    warnings = []
    
    # 1. Daily Overload Check
    daily_load = get_user_daily_load(user_id, date, organization_id, exclude_task_id)
    if daily_load > EFFECTIVE_WORK_HOURS:
        warnings.append({
            "type": "daily_overload",
            "message": f"{user_name} is overloaded on {date.strftime('%Y-%m-%d')} ({daily_load:.2f} hours assigned, effective limit is {EFFECTIVE_WORK_HOURS} hours)."
        })

    # 2. Weekly Overload Check
    weekly_load = get_user_weekly_load(user_id, date, organization_id, exclude_task_id)
    weekly_limit = EFFECTIVE_WORK_HOURS * 5.0
    if weekly_load > weekly_limit:
        warnings.append({
            "type": "weekly_overload",
            "message": f"{user_name} is overloaded for the week of {date.strftime('%Y-%m-%d')} ({weekly_load:.2f} hours assigned, weekly limit is {weekly_limit} hours)."
        })

    # 3. Approved Leave Check
    from users.models import LeaveRequest
    overlapping_leaves = LeaveRequest.objects.filter(
        user_id=user_id,
        status='Approved',
        start_date__lte=date,
        end_date__gte=date
    )
    if overlapping_leaves.exists():
        leave = overlapping_leaves.first()
        warnings.append({
            "type": "on_leave",
            "message": f"{user_name} is on leave on {date.strftime('%Y-%m-%d')} ({leave.leave_type} Leave)."
        })

    return warnings

def extract_mentions(comment_text):
    """
    Regex helper to extract mentioned users (@email or @username) in comment body.
    """
    import re
    from django.contrib.auth import get_user_model
    if not comment_text:
        return []
    
    # Matches @username or @user@domain.com
    raw_mentions = re.findall(r'@([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|[a-zA-Z0-9._-]+)', comment_text)
    User = get_user_model()
    mentioned_users = []
    
    for mention in raw_mentions:
        user = User.objects.filter(email__iexact=mention).first()
        if not user:
            user = User.objects.filter(first_name__iexact=mention).first()
        if not user:
            user = User.objects.filter(last_name__iexact=mention).first()
        if user:
            mentioned_users.append(user)
            
    return list(set(mentioned_users))
