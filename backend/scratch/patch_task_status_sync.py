import re

with open('c:/Users/saura/ParseOps/backend/tasks/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """        ticket.status = new_status
        ticket.save()

        serializer = TaskTicketSerializer(ticket, context={'request': request})"""

replacement = """        ticket.status = new_status
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
                parent_task.save(update_fields=['status'])

        serializer = TaskTicketSerializer(ticket, context={'request': request})"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/backend/tasks/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("tasks/views.py patched to auto-update parent task status.")
