import re

with open('c:/Users/saura/ParseOps/backend/tasks/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """        # Smart Due Date Calculation Fallback
        if not task.due_date and (task.estimated_hours or task.estimated_minutes):
            from tasks.services import TaskService
            mins = task.estimated_minutes or int(float(task.estimated_hours) * 60)
            calculated_date = TaskService.calculate_ideal_due_date(org.id, assignees, mins)
            if calculated_date:
                task.due_date = calculated_date
                task.save(update_fields=['due_date'])"""

replacement = """        # Smart Due Date Calculation Fallback
        updates = []
        if not task.start_date:
            task.start_date = timezone.now().date()
            updates.append('start_date')
            
        if not task.due_date and (task.estimated_hours or task.estimated_minutes):
            from tasks.services import TaskService
            mins = task.estimated_minutes or int(float(task.estimated_hours) * 60)
            calculated_date = TaskService.calculate_ideal_due_date(org.id, assignees, mins)
            if calculated_date:
                task.due_date = calculated_date.date() if hasattr(calculated_date, 'date') else calculated_date
                updates.append('due_date')
        elif not task.due_date and not task.estimated_hours and not task.estimated_minutes:
            task.due_date = timezone.now().date()
            updates.append('due_date')
            
        if updates:
            task.save(update_fields=updates)"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/backend/tasks/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("tasks/views.py updated to set start_date and due_date automatically.")
