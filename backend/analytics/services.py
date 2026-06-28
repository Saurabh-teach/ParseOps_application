import datetime
from django.utils import timezone
from django.db.models import Count, Q, Avg, F
from tasks.models import Task
from goals.models import Goal
from organizations.models import OrganizationMembership

def get_filter_list(filters, param_name):
    """
    Robust helper to retrieve query parameter as a list,
    handling both multiple keys (members=1&members=2) and comma-separated values (members=1,2).
    """
    if not filters:
        return []
    values = []
    if hasattr(filters, 'getlist'):
        values = filters.getlist(param_name)
        if len(values) == 1 and ',' in values[0]:
            values = values[0].split(',')
    else:
        values = filters.get(param_name, [])
        if isinstance(values, str):
            values = [values]
    
    # Clean up empty strings and spaces
    return [v.strip() for v in values if v and str(v).strip()]

def apply_task_filters(queryset, filters, user, now):
    """
    Applies top-bar filters and advanced filters to a Task queryset.
    """
    if not filters:
        return queryset

    # 1. Member Filter (assignees)
    members = get_filter_list(filters, 'members')
    if members:
        queryset = queryset.filter(assignee_id__in=members)

    # 2. Status Filter
    statuses = get_filter_list(filters, 'statuses')
    if statuses:
        status_q = Q()
        db_statuses = [s for s in statuses if s != 'overdue']
        if db_statuses:
            status_q |= Q(status__in=db_statuses)
        if 'overdue' in statuses:
            status_q |= Q(due_date__lt=now) & ~Q(status='done')
        queryset = queryset.filter(status_q)

    # 3. Priority Filter
    priorities = get_filter_list(filters, 'priorities')
    if priorities:
        queryset = queryset.filter(priority__in=priorities)

    # 4. Goal Filter
    goal_id = filters.get('goal')
    if goal_id and goal_id != 'all' and goal_id != 'None':
        queryset = queryset.filter(goal_id=goal_id)

    # 5. Task Type Filter (issue_type)
    task_types = get_filter_list(filters, 'task_types')
    if task_types:
        queryset = queryset.filter(issue_type__in=task_types)

    # 6. Date Range Filter
    date_range = filters.get('date_range')
    if date_range:
        start_date = None
        end_date = None
        
        if date_range == 'this_week':
            start_date = now - datetime.timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + datetime.timedelta(days=7)
        elif date_range == 'this_month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Find next month
            next_month = (start_date.month % 12) + 1
            next_month_year = start_date.year + (1 if start_date.month == 12 else 0)
            end_date = start_date.replace(month=next_month, year=next_month_year)
        elif date_range == 'last_30_days':
            start_date = now - datetime.timedelta(days=30)
            end_date = now
        elif date_range == 'last_quarter':
            start_date = now - datetime.timedelta(days=90)
            end_date = now
        elif date_range == 'custom':
            start_date_str = filters.get('start_date')
            end_date_str = filters.get('end_date')
            if start_date_str:
                try:
                    start_date = timezone.make_aware(datetime.datetime.strptime(start_date_str.split('T')[0], "%Y-%m-%d"))
                except Exception:
                    pass
            if end_date_str:
                try:
                    end_date = timezone.make_aware(datetime.datetime.strptime(end_date_str.split('T')[0], "%Y-%m-%d"))
                    end_date = end_date.replace(hour=23, minute=59, second=59)
                except Exception:
                    pass
        
        if start_date:
            queryset = queryset.filter(due_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(due_date__lte=end_date)

    # 7. Assignee Type Filter (My Tasks, Tasks I Created, All Tasks)
    assignee_type = filters.get('assignee_type')
    if assignee_type == 'my_tasks':
        queryset = queryset.filter(assignee=user)
    elif assignee_type == 'created_tasks':
        queryset = queryset.filter(created_by=user)

    # 8. Overdue Filter (Only Overdue, Not Overdue)
    overdue_status = filters.get('overdue_status')
    if overdue_status == 'only_overdue':
        queryset = queryset.exclude(status='done').filter(due_date__lt=now)
    elif overdue_status == 'not_overdue':
        # Tasks are not overdue if they are done, have a due date in the future, or no due date at all
        queryset = queryset.exclude(Q(due_date__lt=now) & ~Q(status='done'))

    return queryset

def get_personal_analytics(user, organization, filters=None):
    """
    Returns personal analytics for a normal member (only their own data).
    """
    now = timezone.now()
    # Personal tasks assigned to this user in this org
    tasks = Task.objects.filter(organization=organization, assignee=user, is_deleted=False)
    
    # Force the members filter parameter to only contain the requesting user's ID
    clean_filters = None
    if filters:
        if hasattr(filters, 'copy'):
            clean_filters = filters.copy()
        else:
            clean_filters = dict(filters)
        
        if hasattr(clean_filters, 'setlist'):
            clean_filters.setlist('members', [str(user.id)])
        else:
            clean_filters['members'] = [str(user.id)]
    
    # Apply filters to user's tasks
    tasks = apply_task_filters(tasks, clean_filters, user, now)
    
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='done').count()
    overdue_tasks = tasks.exclude(status='done').filter(due_date__lt=now).count()
    in_progress_tasks = tasks.exclude(status='done').exclude(due_date__lt=now).count()
    
    efficiency = 0
    if total_tasks > 0:
        efficiency = int((completed_tasks / total_tasks) * 100)
        
    # User's goals (either they are owner or have tasks mapped to it)
    # Filter goals count depending on Goal filter if present
    goals_query = Goal.objects.filter(
        Q(organization=organization, owner=user) | 
        Q(tasks__assignee=user)
    ).distinct()
    
    goal_filter_val = filters.get('goal') if filters else None
    if goal_filter_val and goal_filter_val != 'all' and goal_filter_val != 'None':
        goals_query = goals_query.filter(id=goal_filter_val)
        
    user_goals_count = goals_query.count()

    return {
        "role": "member",
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "overdue_tasks": overdue_tasks,
        "in_progress_tasks": in_progress_tasks,
        "efficiency": efficiency,
        "goals_involved": user_goals_count,
    }

def get_team_analytics(organization, filters=None, requesting_user=None):
    """
    Returns team-wide analytics and member-wise breakdown for Admin/Owner.
    """
    now = timezone.now()
    all_tasks = Task.objects.filter(organization=organization, is_deleted=False)
    all_goals = Goal.objects.filter(organization=organization, is_deleted=False)
    
    if requesting_user:
        membership = OrganizationMembership.objects.filter(
            organization=organization, user=requesting_user, is_active=True
        ).first()
        if membership and membership.role not in ['owner', 'admin']:
            all_goals = all_goals.filter(
                Q(visibility_type='organization') |
                Q(sharing_option='organization') |
                Q(created_by=requesting_user) |
                Q(owner=requesting_user) |
                Q(visible_to=requesting_user) |
                Q(assignees=requesting_user) |
                Q(shared_viewers=requesting_user)
            ).distinct()
    
    # Apply Goal filter to Goals count
    goal_filter_val = filters.get('goal') if filters else None
    if goal_filter_val and goal_filter_val != 'all' and goal_filter_val != 'None':
        all_goals = all_goals.filter(id=goal_filter_val)
    
    # Apply all other task filters
    all_tasks = apply_task_filters(all_tasks, filters, requesting_user, now)
    
    overall_total_tasks = all_tasks.count()
    overall_completed = all_tasks.filter(status='done').count()
    overall_overdue = all_tasks.exclude(status='done').filter(due_date__lt=now).count()
    overall_pending = max(0, overall_total_tasks - overall_completed - overall_overdue)
    overall_efficiency = int((overall_completed / overall_total_tasks) * 100) if overall_total_tasks > 0 else 0
    
    # Member-wise breakdown (excluding users who haven't accepted their temp password invite)
    active_memberships = OrganizationMembership.objects.filter(
        organization=organization, 
        is_active=True
    )
    total_members_count = active_memberships.count()
    memberships = active_memberships.select_related('user')
    
    selected_members = get_filter_list(filters, 'members')
    if selected_members:
        memberships = memberships.filter(user_id__in=selected_members)
        
    member_stats = []
    
    for membership in memberships:
        user = membership.user
        if not user:
            continue
            
        u_tasks = all_tasks.filter(assignee=user)
        u_total = u_tasks.count()
        u_completed = u_tasks.filter(status='done').count()
        u_overdue = u_tasks.exclude(status='done').filter(due_date__lt=now).count()
        u_efficiency = int((u_completed / u_total) * 100) if u_total > 0 else 0
        
        task_details = []
        for t in u_tasks.select_related('goal'):
            cat = 'completed' if t.status == 'done' else ('overdue' if t.due_date and t.due_date < now else 'pending')
            task_details.append({
                "id": str(t.id),
                "title": t.title,
                "category": cat,
                "goal_title": t.goal.title if t.goal else "No Goal"
            })
            
        member_stats.append({
            "user_id": user.id,
            "name": f"{user.first_name} {user.last_name}".strip() or user.email,
            "role": membership.role,
            "total_tasks": u_total,
            "completed_tasks": u_completed,
            "pending_tasks": max(0, u_total - u_completed - u_overdue),
            "overdue_tasks": u_overdue,
            "efficiency": u_efficiency,
            "task_details": task_details
        })
        
    # Apply Completion Rate Filter (High, Medium, Low performers)
    completion_rate = filters.get('completion_rate') if filters else None
    if completion_rate:
        if completion_rate == 'high':
            member_stats = [m for m in member_stats if m['efficiency'] >= 70]
        elif completion_rate == 'medium':
            member_stats = [m for m in member_stats if 30 <= m['efficiency'] < 70]
        elif completion_rate == 'low':
            member_stats = [m for m in member_stats if m['efficiency'] < 30]
            
    # Sort member stats by efficiency descending
    member_stats = sorted(member_stats, key=lambda x: x['efficiency'], reverse=True)
    
    return {
        "role": "admin", # or owner
        "overall_total_tasks": overall_total_tasks,
        "overall_completed_tasks": overall_completed,
        "overall_efficiency": overall_efficiency,
        "total_goals": all_goals.count(),
        "total_members": total_members_count,
        "member_stats": member_stats,
    }
