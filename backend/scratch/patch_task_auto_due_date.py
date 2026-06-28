import re

with open('c:/Users/saura/ParseOps/backend/tasks/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# For CreateTaskView
target_create = """        serializer = TaskSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            assigned_at = timezone.now() if assignees else None
            task = serializer.save(
                organization=organization,
                created_by=request.user,
                assigned_at=assigned_at
            )"""

replacement_create = """        serializer = TaskSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            assigned_at = timezone.now() if assignees else None
            task = serializer.save(
                organization=organization,
                created_by=request.user,
                assigned_at=assigned_at
            )
            
            # Smart Due Date Calculation Fallback
            if not task.due_date and (task.estimated_hours or task.estimated_minutes):
                from tasks.services import TaskService
                mins = task.estimated_minutes or int(float(task.estimated_hours) * 60)
                calculated_date = TaskService.calculate_ideal_due_date(organization.id, assignees, mins)
                if calculated_date:
                    task.due_date = calculated_date
                    task.save(update_fields=['due_date'])"""

content = content.replace(target_create, replacement_create)

# For OrgTaskListView
target_list = """        assigned_at = timezone.now() if assignees else None
        task = serializer.save(
            organization=org,
            created_by=self.request.user,
            assigned_at=assigned_at
        )"""

replacement_list = """        assigned_at = timezone.now() if assignees else None
        task = serializer.save(
            organization=org,
            created_by=self.request.user,
            assigned_at=assigned_at
        )
        
        # Smart Due Date Calculation Fallback
        if not task.due_date and (task.estimated_hours or task.estimated_minutes):
            from tasks.services import TaskService
            mins = task.estimated_minutes or int(float(task.estimated_hours) * 60)
            calculated_date = TaskService.calculate_ideal_due_date(org.id, assignees, mins)
            if calculated_date:
                task.due_date = calculated_date
                task.save(update_fields=['due_date'])"""

content = content.replace(target_list, replacement_list)

with open('c:/Users/saura/ParseOps/backend/tasks/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("tasks/views.py patched for auto due date calculation")
