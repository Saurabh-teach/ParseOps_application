import re

with open('c:/Users/saura/ParseOps/backend/tasks/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """        if new_status == 'modified':
            if member and member.role == 'member':
                forbidden_assignees = OrganizationMembership.objects.filter(
                    organization=org,
                    user_id__in=assignees,
                    role__in=['admin', 'owner']
                ).exists()
                if forbidden_assignees:
                    task.delete()
                    raise PermissionDenied("Regular users cannot assign tasks to Admins or Owners.")"""

replacement = """        if new_status == 'modified':
            proposed_date = request.data.get('proposed_date')
            if not proposed_date:
                return Response({"detail": "proposed_date is required when modifying a request."}, status=status.HTTP_400_BAD_REQUEST)
            ext_request.proposed_date = proposed_date

        ext_request.save()

        if new_status == 'approved':
            ext_request.task.due_date = ext_request.requested_date
            ext_request.task.save(update_fields=['due_date'])
        elif new_status == 'modified':
            ext_request.task.due_date = ext_request.proposed_date
            ext_request.task.save(update_fields=['due_date'])

        try:
            from notifications.services import NotificationService
            action_text = "approved" if new_status == 'approved' else ("rejected" if new_status == 'rejected' else "modified")
            NotificationService.send_notification(
                recipient=ext_request.requested_by,
                n_type='task_updated',
                title=f"Extension Request {action_text.capitalize()}",
                message=f"Your extension request for '{ext_request.task.title}' was {action_text}.",
                organization=organization,
                link=f"/workspace/tasks?task={ext_request.task.id}"
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to send extension review notification: {e}")

        serializer = TaskExtensionRequestSerializer(ext_request)
        return Response(serializer.data)"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/backend/tasks/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("tasks/views.py patched to fix TaskExtensionReviewView")
