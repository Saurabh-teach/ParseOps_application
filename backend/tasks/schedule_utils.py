from datetime import datetime, timedelta, time
from django.utils import timezone
from .models import Task

def time_to_minutes(t):
    return t.hour * 60 + t.minute

def minutes_to_time(minutes):
    hours = int(minutes // 60) % 24
    mins = int(minutes % 60)
    return time(hours, mins)

def get_work_schedule(user):
    """
    Returns the user's working schedule in minutes.
    """
    from users.models import UserWorkingSchedule
    schedule = UserWorkingSchedule.objects.filter(user=user).first() if user else None

    if not schedule:
        from datetime import time
        class DefaultSchedule:
            work_start_time = time(10, 0)
            work_end_time = time(19, 0)
            lunch_break_start = time(13, 0)
            lunch_break_end = time(14, 0)
            tea_break_start = time(17, 0)
            tea_break_end = time(17, 30)
        schedule = DefaultSchedule()

    work_start = time_to_minutes(schedule.work_start_time)
    
    lunch_start = time_to_minutes(schedule.lunch_break_start)
    lunch_end = time_to_minutes(schedule.lunch_break_end)
    tea_start = time_to_minutes(schedule.tea_break_start)
    tea_end = time_to_minutes(schedule.tea_break_end)
    
    breaks = []
    if lunch_end > lunch_start:
        breaks.append({'start': lunch_start, 'end': lunch_end})
    if tea_end > tea_start:
        breaks.append({'start': tea_start, 'end': tea_end})
        
    breaks.sort(key=lambda x: x['start'])
    
    if hasattr(schedule, 'work_end_time') and schedule.work_end_time:
        work_end = time_to_minutes(schedule.work_end_time)
    else:
        # Fallback to 9 hours shift
        work_end = work_start + (9 * 60)
    
    return {
        'work_start': work_start,
        'work_end': work_end,
        'breaks': breaks
    }

def add_working_time(start_datetime, duration_hours, user):
    """
    Adds duration (in hours) to start_datetime, skipping breaks and non-working hours.
    """
    if not start_datetime or not duration_hours:
        return start_datetime
        
    schedule = get_work_schedule(user)
    work_start = schedule['work_start']
    work_end = schedule['work_end']
    breaks = schedule['breaks']
    
    local_tz = timezone.get_current_timezone()
    dt = start_datetime.astimezone(local_tz)
    
    remaining_minutes = duration_hours * 60
    
    current_date = dt.date()
    current_time_minutes = time_to_minutes(dt.time())
    
    if current_time_minutes < work_start:
        current_time_minutes = work_start
    
    while remaining_minutes > 0:
        if current_time_minutes >= work_end:
            current_date += timedelta(days=1)
            while current_date.weekday() >= 5: 
                current_date += timedelta(days=1)
            current_time_minutes = work_start
            continue
            
        next_event_minutes = work_end
        in_break = False
        break_end = None
        
        for b in breaks:
            if current_time_minutes >= b['start'] and current_time_minutes < b['end']:
                in_break = True
                break_end = b['end']
                break
            elif current_time_minutes < b['start']:
                if b['start'] < next_event_minutes:
                    next_event_minutes = b['start']
                break
                
        if in_break:
            current_time_minutes = break_end
            continue
            
        block_duration = next_event_minutes - current_time_minutes
        if block_duration >= remaining_minutes:
            current_time_minutes += remaining_minutes
            remaining_minutes = 0
        else:
            current_time_minutes += block_duration
            remaining_minutes -= block_duration

    end_time = minutes_to_time(current_time_minutes)
    end_datetime = datetime.combine(current_date, end_time)
    end_datetime_aware = timezone.make_aware(end_datetime, local_tz)
    
    return end_datetime_aware

def calculate_working_hours(start_datetime, end_datetime, user):
    """
    Calculates the working hours between two datetimes.
    """
    if not start_datetime or not end_datetime or start_datetime >= end_datetime:
        return 0.0
        
    schedule = get_work_schedule(user)
    work_start = schedule['work_start']
    work_end = schedule['work_end']
    breaks = schedule['breaks']
    
    local_tz = timezone.get_current_timezone()
    dt = start_datetime.astimezone(local_tz)
    end_dt = end_datetime.astimezone(local_tz)
    
    total_minutes = 0
    current_date = dt.date()
    current_time_minutes = time_to_minutes(dt.time())
    
    end_date = end_dt.date()
    end_time_minutes = time_to_minutes(end_dt.time())
    
    max_days = 365
    days = 0
    
    while days < max_days:
        days += 1
        is_last_day = (current_date == end_date)
        
        day_end_minutes = end_time_minutes if is_last_day else work_end
        if day_end_minutes > work_end:
            day_end_minutes = work_end
            
        if current_time_minutes < work_start:
            current_time_minutes = work_start
            
        while current_time_minutes < day_end_minutes:
            next_event_minutes = day_end_minutes
            in_break = False
            break_end = None
            
            for b in breaks:
                if current_time_minutes >= b['start'] and current_time_minutes < b['end']:
                    in_break = True
                    break_end = b['end']
                    break
                elif current_time_minutes < b['start']:
                    if b['start'] < next_event_minutes:
                        next_event_minutes = b['start']
                    break
                    
            if in_break:
                current_time_minutes = break_end
                continue
                
            block_duration = next_event_minutes - current_time_minutes
            total_minutes += block_duration
            current_time_minutes += block_duration
            
        if is_last_day:
            break
            
        current_date += timedelta(days=1)
        while current_date.weekday() >= 5:
            current_date += timedelta(days=1)
        current_time_minutes = work_start

    return round(total_minutes / 60.0, 2)

def shift_datetime_working_minutes(start_datetime, minutes_delta, user):
    """
    Shifts a datetime by exact working minutes (can be negative).
    """
    if minutes_delta == 0:
        return start_datetime
        
    schedule = get_work_schedule(user)
    work_start = schedule['work_start']
    work_end = schedule['work_end']
    breaks = schedule['breaks']
    
    local_tz = timezone.get_current_timezone()
    dt = start_datetime.astimezone(local_tz)
    
    remaining_minutes = abs(minutes_delta)
    direction = 1 if minutes_delta > 0 else -1
    
    current_date = dt.date()
    current_time_minutes = time_to_minutes(dt.time())
    
    if direction > 0:
        if current_time_minutes < work_start:
            current_time_minutes = work_start
    else:
        if current_time_minutes > work_end:
            current_time_minutes = work_end
    
    while remaining_minutes > 0:
        if direction > 0:
            if current_time_minutes >= work_end:
                current_date += timedelta(days=1)
                while current_date.weekday() >= 5:
                    current_date += timedelta(days=1)
                current_time_minutes = work_start
                continue
                
            next_event_minutes = work_end
            in_break = False
            break_end = None
            
            for b in breaks:
                if current_time_minutes >= b['start'] and current_time_minutes < b['end']:
                    in_break = True
                    break_end = b['end']
                    break
                elif current_time_minutes < b['start']:
                    if b['start'] < next_event_minutes:
                        next_event_minutes = b['start']
                    break
                    
            if in_break:
                current_time_minutes = break_end
                continue
                
            block_duration = next_event_minutes - current_time_minutes
            if block_duration >= remaining_minutes:
                current_time_minutes += remaining_minutes
                remaining_minutes = 0
            else:
                current_time_minutes += block_duration
                remaining_minutes -= block_duration
        else:
            if current_time_minutes <= work_start:
                current_date -= timedelta(days=1)
                while current_date.weekday() >= 5:
                    current_date -= timedelta(days=1)
                current_time_minutes = work_end
                continue
                
            prev_event_minutes = work_start
            in_break = False
            break_start = None
            
            for b in reversed(breaks):
                if current_time_minutes > b['start'] and current_time_minutes <= b['end']:
                    in_break = True
                    break_start = b['start']
                    break
                elif current_time_minutes > b['end']:
                    if b['end'] > prev_event_minutes:
                        prev_event_minutes = b['end']
                    break
                    
            if in_break:
                current_time_minutes = break_start
                continue
                
            block_duration = current_time_minutes - prev_event_minutes
            if block_duration >= remaining_minutes:
                current_time_minutes -= remaining_minutes
                remaining_minutes = 0
            else:
                current_time_minutes -= block_duration
                remaining_minutes -= block_duration

    end_time = minutes_to_time(current_time_minutes)
    end_datetime = datetime.combine(current_date, end_time)
    # Adding zero working minutes via add_working_time will snap to valid position
    return add_working_time(dt, 0, user)
def _snap_to_working_time(dt, user):
    return add_working_time(dt, 0, user)

def find_earliest_gap(assignee, duration_hours, search_start_datetime=None):
    """
    Finds the earliest available gap for the assignee that can fit duration_hours.
    Returns the start of the earliest valid slot, or None if capacity is exceeded.
    """
    if not search_start_datetime:
        search_start_datetime = timezone.now()

    # Snap the search start to the next valid working moment
    search_start_datetime = _snap_to_working_time(search_start_datetime, assignee)

    tasks = Task.objects.filter(
        assignee=assignee,
        status__in=['todo', 'in_progress'],
        planned_end__gte=search_start_datetime
    ).order_by('planned_start')

    current_time = search_start_datetime
    for task in tasks:
        if task.planned_start > current_time:
            snapped = _snap_to_working_time(current_time, assignee)
            gap_hours = calculate_working_hours(snapped, task.planned_start, assignee)
            if gap_hours >= duration_hours:
                if calculate_working_hours(search_start_datetime, snapped, assignee) > 56:
                    return None
                return snapped
        current_time = max(current_time, task.planned_end)

    snapped = _snap_to_working_time(current_time, assignee)
    if calculate_working_hours(search_start_datetime, snapped, assignee) > 56:
        return None
    return snapped

