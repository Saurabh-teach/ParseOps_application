import re

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """    @action(detail=False, methods=['get'], url_path='my-workspaces')"""

replacement = """    @action(detail=True, methods=['get'], url_path='calendar-events')
    def calendar_events(self, request, pk=None):
        org = self.get_object()
        membership = get_object_or_404(OrganizationMembership, organization=org, user=request.user, is_active=True)
        is_manager = membership.role in ['admin', 'owner']

        start_date = request.query_params.get('start')
        end_date = request.query_params.get('end')

        from tasks.models import Task
        from goals.models import Goals
        from django.db.models import Q
        import datetime

        # Tasks Query
        task_query = Q(organization=org, is_deleted=False)
        if not is_manager:
            task_query &= Q(assignees=request.user)

        if start_date and end_date:
            try:
                s_dt = datetime.datetime.strptime(start_date[:10], '%Y-%m-%d')
                e_dt = datetime.datetime.strptime(end_date[:10], '%Y-%m-%d')
                task_query &= (Q(due_date__gte=s_dt) | Q(start_date__lte=e_dt))
            except ValueError:
                pass

        tasks = Task.objects.filter(task_query).distinct()

        # Goals Query
        goal_query = Q(organization=org)
        if not is_manager:
            goal_query &= Q(owners=request.user)

        if start_date and end_date:
            try:
                s_dt = datetime.datetime.strptime(start_date[:10], '%Y-%m-%d').date()
                e_dt = datetime.datetime.strptime(end_date[:10], '%Y-%m-%d').date()
                goal_query &= (Q(end_date__gte=s_dt) | Q(start_date__lte=e_dt))
            except ValueError:
                pass

        goals = Goals.objects.filter(goal_query).distinct()

        events = []
        for t in tasks:
            start = t.start_date.isoformat() if t.start_date else (t.created_at.date().isoformat() if t.created_at else None)
            end = t.due_date.isoformat() if t.due_date else start
            color = '#fef08a' if t.priority == 'urgent' else ('#fecaca' if t.priority == 'high' else ('#bfdbfe' if t.priority == 'medium' else '#d9f99d'))
            events.append({
                'id': f"task_{t.id}",
                'title': f"[Task] {t.title}",
                'start': start,
                'end': end,
                'allDay': False if t.due_date and t.due_date.hour > 0 else True,
                'backgroundColor': color,
                'borderColor': color,
                'textColor': '#0f172a',
                'extendedProps': {
                    'type': 'task',
                    'original_id': str(t.id),
                    'status': t.status,
                    'priority': t.priority,
                    'estimated_hours': float(t.estimated_hours) if t.estimated_hours else (t.estimated_minutes/60.0 if t.estimated_minutes else 0)
                }
            })

        for g in goals:
            start = g.start_date.isoformat() if g.start_date else None
            end = g.end_date.isoformat() if g.end_date else start
            events.append({
                'id': f"goal_{g.id}",
                'title': f"[Goal] {g.title}",
                'start': start,
                'end': end,
                'allDay': True,
                'backgroundColor': '#c084fc',
                'borderColor': '#a855f7',
                'textColor': '#ffffff',
                'extendedProps': {
                    'type': 'goal',
                    'original_id': str(g.id),
                    'status': g.status,
                    'progress': g.progress
                }
            })

        return Response(events)

    @action(detail=False, methods=['get'], url_path='my-workspaces')"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("organizations/views.py patched for calendar API")
