import logging
from datetime import datetime, timedelta, time
from django.utils import timezone

try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo

logger = logging.getLogger(__name__)

def to_org_tz(dt: datetime, organization) -> datetime:
    tz = zoneinfo.ZoneInfo(organization.timezone)
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, tz)
    return dt.astimezone(tz)

def is_working_day(day, organization, leave_dates=None) -> bool:
    working_days = organization.working_days
    # If not set, default to Mon-Fri (0-4)
    if not working_days:
        working_days = [0, 1, 2, 3, 4]
    return day.weekday() in working_days and (not leave_dates or day not in leave_dates)

def get_working_intervals(day, organization, user=None):
    org_tz = zoneinfo.ZoneInfo(organization.timezone)
    
    schedule = None
    if user:
        from users.models import UserWorkingSchedule
        schedule = UserWorkingSchedule.objects.filter(user=user).first()

    w_start = getattr(schedule, 'work_start_time', None) or organization.working_start_time
    w_end = getattr(schedule, 'work_end_time', None) or organization.working_end_time
    l_start = getattr(schedule, 'lunch_break_start', None) or organization.lunch_break_start
    l_end = getattr(schedule, 'lunch_break_end', None) or organization.lunch_break_end
    t_start = getattr(schedule, 'tea_break_start', None) or organization.tea_break_start
    t_end = getattr(schedule, 'tea_break_end', None) or organization.tea_break_end

    start_dt = datetime.combine(day, w_start, tzinfo=org_tz)
    end_dt = datetime.combine(day, w_end, tzinfo=org_tz)
    if w_end < w_start:
        end_dt += timedelta(days=1)
    
    def normalize_break(t, day_dt):
        dt = datetime.combine(day_dt, t, tzinfo=org_tz)
        if t < w_start:
            dt += timedelta(days=1)
        return dt
        
    lunch_start = normalize_break(l_start, day)
    lunch_end = normalize_break(l_end, day)
    tea_start = normalize_break(t_start, day)
    tea_end = normalize_break(t_end, day)
    
    # Clamp standard breaks to working hours
    lunch_start = max(start_dt, min(lunch_start, end_dt))
    lunch_end = max(start_dt, min(lunch_end, end_dt))
    tea_start = max(start_dt, min(tea_start, end_dt))
    tea_end = max(start_dt, min(tea_end, end_dt))
    
    breaks = []
    
    no_lunch = getattr(schedule, 'no_lunch_break', False) if schedule else False
    no_tea = getattr(schedule, 'no_tea_break', False) if schedule else False
    
    if not no_lunch and lunch_start < lunch_end:
        breaks.append((lunch_start, lunch_end))
    if not no_tea and tea_start < tea_end:
        breaks.append((tea_start, tea_end))
    
    for extra_break in organization.additional_breaks:
        try:
            if isinstance(extra_break, dict) and 'start' in extra_break and 'end' in extra_break:
                b_s_time = time.fromisoformat(extra_break['start'])
                b_e_time = time.fromisoformat(extra_break['end'])
                
                b_start = normalize_break(b_s_time, day)
                b_end = normalize_break(b_e_time, day)
                
                # Clamp additional breaks to working hours
                b_start = max(start_dt, min(b_start, end_dt))
                b_end = max(start_dt, min(b_end, end_dt))
                
                if b_start < b_end:
                    breaks.append((b_start, b_end))
        except Exception:
            pass
            
    breaks.sort(key=lambda x: x[0])
    
    intervals = []
    current = start_dt
    for b_start, b_end in breaks:
        if b_start > current:
            intervals.append((current, b_start))
        current = max(current, b_end)
    
    if current < end_dt:
        intervals.append((current, end_dt))
        
    return intervals

def next_working_day_start(day, organization, leave_dates=None, user=None) -> datetime:
    next_day = day + timedelta(days=1)
    while not is_working_day(next_day, organization, leave_dates):
        next_day += timedelta(days=1)
    org_tz = zoneinfo.ZoneInfo(organization.timezone)
    schedule = None
    if user:
        from users.models import UserWorkingSchedule
        schedule = UserWorkingSchedule.objects.filter(user=user).first()
    w_start = getattr(schedule, 'work_start_time', None) or organization.working_start_time
    return datetime.combine(next_day, w_start, tzinfo=org_tz)

def add_working_hours(start_time: datetime, hours_to_add: float, organization, leave_dates=None, user=None) -> datetime:
    """
    Adds business hours to a start_time respecting organization schedule.
    """
    current_time = to_org_tz(start_time, organization).replace(second=0, microsecond=0)
    remaining_mins = int(round(hours_to_add * 60))

    while remaining_mins > 0:
        current_time = adjust_to_working_hours(current_time, organization, leave_dates=leave_dates, user=user)
        day = current_time.date()

        for interval_start, interval_end in get_working_intervals(day, organization, user=user):
            if interval_end <= current_time:
                continue

            active_start = max(interval_start, current_time)
            available_mins = int(round((interval_end - active_start).total_seconds() / 60.0))

            if available_mins >= remaining_mins:
                current_time = active_start + timedelta(minutes=remaining_mins)
                remaining_mins = 0
                break

            remaining_mins -= available_mins
            current_time = interval_end

        if remaining_mins > 0:
            current_time = next_working_day_start(day, organization, leave_dates=leave_dates, user=user)

    return current_time

def previous_working_day_end(day, organization, leave_dates=None, user=None) -> datetime:
    prev_day = day - timedelta(days=1)
    while not is_working_day(prev_day, organization, leave_dates):
        prev_day -= timedelta(days=1)
    org_tz = zoneinfo.ZoneInfo(organization.timezone)
    schedule = None
    if user:
        from users.models import UserWorkingSchedule
        schedule = UserWorkingSchedule.objects.filter(user=user).first()
    w_end = getattr(schedule, 'work_end_time', None) or organization.working_end_time
    return datetime.combine(prev_day, w_end, tzinfo=org_tz)

def subtract_working_hours(start_time: datetime, hours_to_subtract: float, organization, leave_dates=None, user=None) -> datetime:
    current_time = to_org_tz(start_time, organization).replace(second=0, microsecond=0)
    remaining_mins = int(round(hours_to_subtract * 60))

    while remaining_mins > 0:
        day = current_time.date()
        if not is_working_day(day, organization, leave_dates):
            current_time = previous_working_day_end(day, organization, leave_dates, user=user)
            continue
            
        intervals = get_working_intervals(day, organization, user=user)
        if not intervals:
            current_time = previous_working_day_end(day, organization, leave_dates, user=user)
            continue
            
        if current_time <= intervals[0][0]:
            current_time = previous_working_day_end(day, organization, leave_dates, user=user)
            continue

        for interval_start, interval_end in reversed(intervals):
            if current_time <= interval_start:
                continue

            active_end = min(interval_end, current_time)
            available_mins = int(round((active_end - interval_start).total_seconds() / 60.0))

            if available_mins >= remaining_mins:
                current_time = active_end - timedelta(minutes=remaining_mins)
                remaining_mins = 0
                break

            remaining_mins -= available_mins
            current_time = interval_start

        if remaining_mins > 0:
            current_time = previous_working_day_end(day, organization, leave_dates, user=user)

    return current_time

def shift_working_hours(start_time: datetime, delta_hours: float, organization, leave_dates=None, user=None) -> datetime:
    if delta_hours == 0:
        return start_time
    elif delta_hours > 0:
        return add_working_hours(start_time, delta_hours, organization, leave_dates, user)
    else:
        return subtract_working_hours(start_time, -delta_hours, organization, leave_dates, user)

def calculate_working_hours(start_time: datetime, end_time: datetime, organization, leave_dates=None, user=None) -> float:
    """
    Calculates the exact working hours between start_time and end_time respecting organization schedule.
    """
    if not start_time or not end_time or start_time >= end_time:
        return 0.0

    current_time = to_org_tz(start_time, organization).replace(second=0, microsecond=0)
    end_time_tz = to_org_tz(end_time, organization).replace(second=0, microsecond=0)
    
    total_mins = 0

    while current_time < end_time_tz:
        day = current_time.date()
        if not is_working_day(day, organization, leave_dates):
            current_time = next_working_day_start(day, organization, leave_dates=leave_dates, user=user)
            continue
            
        intervals = get_working_intervals(day, organization, user=user)
        if not intervals:
            current_time = next_working_day_start(day, organization, leave_dates=leave_dates, user=user)
            continue

        for interval_start, interval_end in intervals:
            if interval_end <= current_time:
                continue

            active_start = max(interval_start, current_time)
            
            if active_start >= end_time_tz:
                return total_mins / 60.0
                
            active_end = min(interval_end, end_time_tz)
            
            if active_end > active_start:
                total_mins += int(round((active_end - active_start).total_seconds() / 60.0))
            
            current_time = interval_end

        if current_time < end_time_tz:
            current_time = next_working_day_start(day, organization, leave_dates=leave_dates, user=user)

    return total_mins / 60.0

def adjust_to_working_hours(dt: datetime, organization, leave_dates=None, user=None) -> datetime:
    current_time = to_org_tz(dt, organization)
    while True:
        day = current_time.date()
        if not is_working_day(day, organization, leave_dates):
            current_time = next_working_day_start(day, organization, leave_dates=leave_dates, user=user)
            continue

        intervals = get_working_intervals(day, organization, user=user)
        if not intervals:
            current_time = next_working_day_start(day, organization, leave_dates=leave_dates, user=user)
            continue
            
        if current_time < intervals[0][0]:
            return intervals[0][0]

        moved = False
        for interval_start, interval_end in intervals:
            if interval_start <= current_time < interval_end:
                return current_time
            if current_time < interval_start:
                current_time = interval_start
                moved = True
                break

        if moved:
            continue

        current_time = next_working_day_start(day, organization, leave_dates=leave_dates, user=user)
    return current_time

def get_end_of_working_days_window(start_time: datetime, days: int, organization, leave_dates=None) -> datetime:
    current = to_org_tz(start_time, organization)
    working_days_counted = 0
    temp_date = current.date()
    
    is_workday = is_working_day(temp_date, organization, leave_dates)
    if is_workday and current.time() < organization.working_end_time:
        working_days_counted = 1
    else:
        working_days_counted = 0
        
    while working_days_counted < days:
        temp_date += timedelta(days=1)
        if is_working_day(temp_date, organization, leave_dates):
            working_days_counted += 1
            
    org_tz = zoneinfo.ZoneInfo(organization.timezone)
    return datetime.combine(temp_date, organization.working_end_time, tzinfo=org_tz)
