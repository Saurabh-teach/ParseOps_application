import re

with open('c:/Users/saura/ParseOps/backend/tasks/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """        new_status = request.data.get('status')
        if not new_status:
            return Response({"status": "This field is required."}, status=status.HTTP_400_BAD_REQUEST)

        valid_statuses = [c[0] for c in Task.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response({"status": f"Invalid status. Must be one of {valid_statuses}."}, status=status.HTTP_400_BAD_REQUEST)

        ticket.status = new_status
        ticket.save()
        
        # Auto-update parent task status if applicable
        parent_task = ticket.task
        if new_status == 'in_progress' and parent_task.status == 'todo':
            parent_task.status = 'in_progress'
            parent_task.save(update_fields=['status'])
        elif new_status == 'in_review' and parent_task.status in ['todo', 'in_progress']:
            # Check if all tickets are in review or done
            all_tickets = parent_task.tickets.all()
            if all(t.status in ['in_review', 'done'] for t in all_tickets):
                parent_task.status = 'in_review'
                parent_task.save(update_fields=['status'])"""

replacement = """        new_status = request.data.get('status')
        add_time = request.data.get('add_time_minutes')
        
        if not new_status and add_time is None:
            return Response({"detail": "Provide status or add_time_minutes."}, status=status.HTTP_400_BAD_REQUEST)

        if new_status:
            valid_statuses = [c[0] for c in Task.STATUS_CHOICES]
            if new_status not in valid_statuses:
                return Response({"status": f"Invalid status. Must be one of {valid_statuses}."}, status=status.HTTP_400_BAD_REQUEST)
            ticket.status = new_status
            
        if add_time:
            try:
                ticket.time_spent_minutes += int(add_time)
            except ValueError:
                return Response({"detail": "add_time_minutes must be an integer."}, status=status.HTTP_400_BAD_REQUEST)

        ticket.save()
        
        # Auto-update parent task status if applicable
        if new_status:
            parent_task = ticket.task
            if new_status == 'in_progress' and parent_task.status == 'todo':
                parent_task.status = 'in_progress'
                parent_task.save(update_fields=['status'])
            elif new_status == 'in_review' and parent_task.status in ['todo', 'in_progress']:
                # Check if all tickets are in review or done
                all_tickets = parent_task.tickets.all()
                if all(t.status in ['in_review', 'done'] for t in all_tickets):
                    parent_task.status = 'in_review'
                    parent_task.save(update_fields=['status'])"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/backend/tasks/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("tasks/views.py patched to support add_time_minutes")
