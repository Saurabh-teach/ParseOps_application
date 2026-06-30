from django.db.models.signals import post_save, pre_save, pre_delete, m2m_changed
from django.dispatch import receiver
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from tasks.models import Task, TaskComment
from notifications.services import NotificationService
from chat.models import ChatRoom, ChatParticipant

def get_user_display_name(user):
    """
    Returns the user's First Name + Last Name if available, otherwise email.
    """
    if user:
        if user.first_name or user.last_name:
            return f"{user.first_name} {user.last_name}".strip()
        return user.email
    return "Someone"

def get_task_recipients(task, include_creator=False):
    """
    Collects all unique users relevant to a task: assignees, watchers, goal owner, and optionally creator.
    """
    recipients = set()
    
    # 1. Assignee (single)
    if task.assignee:
        recipients.add(task.assignee)
    
    # 2. Watchers
    for user in task.watchers.all():
        recipients.add(user)
    
    # 3. Goal Owner
    if task.goal and task.goal.owner:
        recipients.add(task.goal.owner)
    
    # 4. Creator
    if include_creator and task.created_by:
        recipients.add(task.created_by)
    
    return list(recipients)

def notify_task_created(task_id):
    try:
        task = Task.objects.select_related('goal', 'goal__owner', 'created_by', 'assignee').prefetch_related('watchers').get(id=task_id)
    except Task.DoesNotExist:
        return
        
    recipients = get_task_recipients(task, include_creator=False)
    title = "New Task Created"
    link = f"/tasks/{task.id}"
    
    for recipient in recipients:
        recipient_name = get_user_display_name(recipient)
        creator_name = get_user_display_name(task.created_by)
        message = f"Hello {recipient_name}, a new task '{task.title}' has been created by {creator_name} in your workspace."
        NotificationService.send_notification(
            recipient=recipient,
            n_type="task_created",
            title=title,
            message=message,
            link=link,
            organization=task.organization
        )

def notify_task_completed(task_id, actor=None):
    try:
        task = Task.objects.select_related('goal', 'goal__owner', 'created_by', 'assignee').prefetch_related('watchers').get(id=task_id)
    except Task.DoesNotExist:
        return
        
    recipients = get_task_recipients(task, include_creator=True)
    actor_name = get_user_display_name(actor or task.created_by)
    title = "Task Completed"
    link = f"/tasks/{task.id}"
    
    for recipient in recipients:
        recipient_name = get_user_display_name(recipient)
        message = f"Hello {recipient_name}, task '{task.title}' has been completed by {actor_name}."
        NotificationService.send_notification(
            recipient=recipient,
            n_type="task_completed",
            title=title,
            message=message,
            link=link,
            organization=task.organization
        )

def notify_task_updated(task_id, actor=None):
    try:
        task = Task.objects.select_related('goal', 'goal__owner', 'created_by', 'assignee').prefetch_related('watchers').get(id=task_id)
    except Task.DoesNotExist:
        return
        
    recipients = get_task_recipients(task, include_creator=True)
    actor_name = get_user_display_name(actor or task.created_by)
    title = "Task Updated"
    link = f"/tasks/{task.id}"
    status_display = task.get_status_display()
    
    for recipient in recipients:
        recipient_name = get_user_display_name(recipient)
        message = f"Hello {recipient_name}, task '{task.title}' has been updated to '{status_display}' by {actor_name}."
        NotificationService.send_notification(
            recipient=recipient,
            n_type="task_updated",
            title=title,
            message=message,
            link=link,
            organization=task.organization
        )

def notify_task_deleted_immediate(task, actor=None):
    recipients = get_task_recipients(task, include_creator=True)
    actor_name = get_user_display_name(actor)
    title = "Task Deleted"
    
    for recipient in recipients:
        recipient_name = get_user_display_name(recipient)
        message = f"Hello {recipient_name}, task '{task.title}' has been deleted by {actor_name}."
        NotificationService.send_notification(
            recipient=recipient,
            n_type="task_deleted",
            title=title,
            message=message,
            link=None,
            organization=task.organization
        )

@receiver(pre_save, sender=Task)
def track_task_changes(sender, instance, **kwargs):
    from tasks.services.scheduler import SchedulerService
    if SchedulerService.is_running():
        instance._was_deleted = False
        instance._old_status = None
        instance._user_facing_changed = False
        instance._reschedule_needed = False
        instance._old_assignee_id = None
        return

    # If task becomes done, make sure schedule_status is COMPLETED
    if instance.status == 'done':
        instance.schedule_status = 'COMPLETED'
        update_fields = kwargs.get('update_fields')
        if update_fields is not None:
            update_fields = set(update_fields)
            update_fields.add('schedule_status')
            kwargs['update_fields'] = list(update_fields)
            
    if instance.pk:
        try:
            orig = Task.objects.get(pk=instance.pk)
            instance._was_deleted = orig.is_deleted
            instance._old_status = orig.status
            instance._user_facing_changed = (
                orig.title != instance.title or
                orig.description != instance.description or
                orig.due_date != instance.due_date or
                orig.priority != instance.priority or
                orig.status != instance.status
            )
            
            # If status changes from done back to something else, reset schedule_status to QUEUED
            if orig.status == 'done' and instance.status != 'done':
                instance.schedule_status = 'QUEUED'
                instance.planned_start = None
                instance.planned_end = None
                update_fields = kwargs.get('update_fields')
                if update_fields is not None:
                    update_fields = set(update_fields)
                    update_fields.update(['schedule_status', 'planned_start', 'planned_end'])
                    kwargs['update_fields'] = list(update_fields)

            # Check if reschedule of assignee is needed
            instance._old_assignee_id = orig.assignee_id
            assignee_changed = orig.assignee_id != instance.assignee_id
            
            if assignee_changed and instance.schedule_status == 'SCHEDULED':
                instance.schedule_status = 'QUEUED'
                instance.planned_start = None
                instance.planned_end = None
                update_fields = kwargs.get('update_fields')
                if update_fields is not None:
                    update_fields = set(update_fields)
                    update_fields.update(['schedule_status', 'planned_start', 'planned_end'])
                    kwargs['update_fields'] = list(update_fields)
            
            instance._reschedule_needed = (
                assignee_changed or
                orig.estimated_hours != instance.estimated_hours or
                orig.estimated_minutes != instance.estimated_minutes or
                orig.due_date != instance.due_date or
                orig.priority != instance.priority or
                orig.status != instance.status or
                getattr(orig, 'risk', None) != getattr(instance, 'risk', None) or
                orig.is_deleted != instance.is_deleted
            )
            if getattr(instance, '_skip_dynamic_reschedule', False):
                # Task detail saves run an explicit SchedulerService cascade
                # after the transaction commits. Do not also run the broad
                # signal rescheduler, or earlier tasks can be repacked.
                instance._reschedule_needed = False
            instance._old_planned_start = orig.planned_start

            
            # Compute actual hours from tickets if not set and status changes to done
            if instance.status == 'done' and orig.status != 'done':
                if not instance.actual_hours:
                    total_mins = sum(ticket.time_spent_minutes for ticket in instance.tickets.all())
                    instance.actual_time_spent_minutes = total_mins
                    instance.actual_hours = total_mins / 60.0
        except Task.DoesNotExist:
            instance._was_deleted = False
            instance._old_status = None
            instance._user_facing_changed = False
            instance._reschedule_needed = False
            instance._old_assignee_id = None
    else:
        instance._was_deleted = False
        instance._old_status = None
        instance._user_facing_changed = False
        instance._reschedule_needed = False
        instance._old_assignee_id = None

@receiver(post_save, sender=Task)
def handle_task_save(sender, instance, created, **kwargs):
    from tasks.services.scheduler import SchedulerService
    if SchedulerService.is_running():
        return

    # Invalidate assignee occupied intervals cache
    from tasks.services import invalidate_assignee_occupied_cache
    if instance.assignee_id:
        invalidate_assignee_occupied_cache(instance.assignee_id)
    old_assignee_id = getattr(instance, '_old_assignee_id', None)
    if old_assignee_id and old_assignee_id != instance.assignee_id:
        invalidate_assignee_occupied_cache(old_assignee_id)

    # Retrieve current request user if set dynamically, or default to None
    actor = getattr(instance, '_current_user', None) or instance.created_by
    if created:
        transaction.on_commit(lambda: notify_task_created(instance.id))
        
        # If task was created with an assignee, trigger scheduling for them
        if instance.assignee_id:
            assignee_id = instance.assignee_id
            org_id = instance.organization_id
            def do_initial_scheduling():
                from tasks.services.scheduler import reschedule_assignee_tasks
                reschedule_assignee_tasks(assignee_id, org_id)
            transaction.on_commit(do_initial_scheduling)
    else:
        was_deleted = getattr(instance, '_was_deleted', False)
        old_status = getattr(instance, '_old_status', None)
        user_facing_changed = getattr(instance, '_user_facing_changed', False)
        
        # Reschedule assignee tasks if needed
        reschedule_needed = (
            getattr(instance, '_reschedule_needed', False) and
            not getattr(instance, '_skip_dynamic_reschedule', False)
        )
        if reschedule_needed:
            old_assignee_id = getattr(instance, '_old_assignee_id', None)
            new_assignee_id = instance.assignee_id
            org_id = instance.organization_id
            old_planned_start = getattr(instance, '_old_planned_start', None)
            
            def do_rescheduling():
                from tasks.services.scheduler import reschedule_assignee_tasks, reschedule_from_datetime
                # Handle old assignee's schedule
                if old_assignee_id:
                    if old_planned_start:
                        reschedule_from_datetime(old_assignee_id, org_id, old_planned_start)
                    else:
                        reschedule_assignee_tasks(old_assignee_id, org_id)
                
                # Handle new assignee's schedule
                if new_assignee_id:
                    # If assignee didn't change but it was scheduled, the old_assignee_id block above
                    # already triggered reschedule_from_datetime for this user, so we don't need to do it twice.
                    if new_assignee_id != old_assignee_id:
                        reschedule_assignee_tasks(new_assignee_id, org_id)
                        
            transaction.on_commit(do_rescheduling)
            
        update_fields = kwargs.get('update_fields')
        is_background_update = update_fields and not any(f in update_fields for f in ['title', 'description', 'due_date', 'priority', 'status'])
        
        assignee_changed = getattr(instance, '_old_assignee_id', None) != getattr(instance, 'assignee_id', None)
        if assignee_changed and instance.assignee_id and not is_background_update:
            transaction.on_commit(lambda: notify_task_assigned(instance.id, instance.assignee_id, actor))
            
        if instance.is_deleted and not was_deleted:
            def on_delete_actions():
                notify_task_deleted_immediate(instance, actor)
                if instance.assignee_id and instance.planned_start:
                    from tasks.services.scheduler import reschedule_from_datetime
                    reschedule_from_datetime(instance.assignee_id, instance.organization_id, instance.planned_start)
            transaction.on_commit(on_delete_actions)
        elif not instance.is_deleted and was_deleted:
            transaction.on_commit(lambda: notify_task_updated(instance.id, actor))
        elif not instance.is_deleted:
            if instance.status == 'done' and old_status != 'done':
                transaction.on_commit(lambda: notify_task_completed(instance.id, actor))
                
                # Perform post-completion actions: update metrics and trigger rescheduling
                if instance.assignee:
                    assignee_id = instance.assignee.id
                    org_id = instance.organization.id
                    
                    def on_complete_actions():
                        from django.contrib.auth import get_user_model
                        from tasks.services.scheduler import reschedule_from_datetime, reschedule_assignee_tasks
                        from django.utils import timezone
                        
                        try:
                            # Pull tasks forward from where this task was supposed to start
                            if instance.planned_start:
                                reschedule_from_datetime(assignee_id, org_id, instance.planned_start)
                            else:
                                reschedule_assignee_tasks(assignee_id, org_id)
                        except Exception:
                            pass
                            
                    transaction.on_commit(on_complete_actions)
            elif user_facing_changed and not is_background_update:
                transaction.on_commit(lambda: notify_task_updated(instance.id, actor))


# Removed m2m_changed handler for assignees as Task now uses a single assignee field.

def notify_task_assigned(task_id, assignee_id, actor=None):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        task = Task.objects.get(id=task_id)
        assignee = User.objects.get(id=assignee_id)
    except (Task.DoesNotExist, User.DoesNotExist):
        return

    title = "New Task Assigned"
    link = f"/tasks/{task.id}"
    actor_name = get_user_display_name(actor) if actor else "workspace admin"
    
    user_name = get_user_display_name(assignee)
    message = f"Hello {user_name}, you have been assigned to task '{task.title}' by {actor_name}."
    NotificationService.send_notification(
        recipient=assignee,
        n_type="task_assigned",
        title=title,
        message=message,
        link=link,
        organization=task.organization
    )

def notify_task_rescheduled(task_id):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return
        
    if not task.assignee:
        return

    title = "Task Rescheduled"
    link = f"/tasks/{task.id}"
    user_name = get_user_display_name(task.assignee)
    message = f"Hello {user_name}, your task '{task.title}' has been automatically rescheduled to start on {task.planned_start.strftime('%b %d, %I:%M %p')}."
    
    NotificationService.send_notification(
        recipient=task.assignee,
        n_type="task_rescheduled",
        title=title,
        message=message,
        link=link,
        organization=task.organization
    )

@receiver(pre_delete, sender=Task)
def handle_task_pre_delete(sender, instance, **kwargs):
    if instance.assignee_id:
        from tasks.services import invalidate_assignee_occupied_cache
        invalidate_assignee_occupied_cache(instance.assignee_id)

    if not instance.is_deleted:
        actor = getattr(instance, '_current_user', None)
        notify_task_deleted_immediate(instance, actor)

def detect_time_based_notifications():
    """
    Utility function to detect overdue and due soon tasks.
    Can be run via a Celery Beat task or a cron job.
    """
    now = timezone.now()
    
    # 1. Overdue Detection
    # If due_date < now and is_overdue is False and status is not done
    overdue_tasks = Task.objects.filter(
        is_overdue=False,
        is_deleted=False,
        due_date__lt=now
    ).exclude(status='done')

    for task in overdue_tasks:
        task.is_overdue = True
        task.save(update_fields=['is_overdue'])
        _notify_time_based(task, "Task Overdue", "overdue")
        


    # 3. Auto-Pause (Idle Timeout)
    from tasks.models import TaskTicket
    eight_hours_ago = now - timedelta(hours=8)
    idle_tickets = TaskTicket.objects.filter(
        status='in_progress',
        updated_at__lt=eight_hours_ago
    ).select_related('task', 'assignee')
    
    for ticket in idle_tickets:
        ticket.status = 'todo'
        ticket.time_spent_minutes += 8 * 60
        ticket.save(update_fields=['status', 'time_spent_minutes', 'updated_at'])
        NotificationService.send_notification(
            recipient=ticket.assignee,
            n_type="task_auto_paused",
            title="Task Auto-Paused",
            message=f"Your ticket for '{ticket.task.title}' was automatically paused after 8 hours of continuous tracking.",
            organization=ticket.task.organization,
            link=f"/workspace/tasks?task={ticket.task.id}"
        )

    # 4. Manager Alerts for Over Time
    from notifications.models import Notification
    active_tickets = TaskTicket.objects.filter(status='in_progress').select_related('task', 'assignee')
    for ticket in active_tickets:
        task = ticket.task
        task_mins = task.total_estimated_minutes
        if task_mins == 60 and not task.estimated_hours and not task.estimated_minutes:
            continue
            
        num_assignees = 1 if task.assignee else 0
        assigned_mins = task_mins // max(num_assignees, 1)
        
        elapsed_minutes = int((now - ticket.updated_at).total_seconds() / 60)
        total_minutes = ticket.time_spent_minutes + elapsed_minutes
        
        if total_minutes >= assigned_mins:
            # Check if notification was already sent today
            recently_notified = Notification.objects.filter(
                user=ticket.assignee,
                notification_type='over_time_alert',
                message__contains=str(assigned_mins),
                created_at__gte=now - timedelta(hours=24)
            ).exists()
            
            if not recently_notified:
                NotificationService.send_notification(
                    recipient=ticket.assignee,
                    n_type='over_time_alert',
                    title=f"⚠️ Over Time: {task.title}",
                    message=f"You have exceeded your assigned {assigned_mins}m budget for this task.",
                    organization=task.organization,
                    link=f"/workspace/tasks?task={task.id}"
                )
                
                # Also notify the manager/creator if they are different from the assignee
                if task.created_by and task.created_by != ticket.assignee:
                    NotificationService.send_notification(
                        recipient=task.created_by,
                        n_type='over_time_alert_manager',
                        title=f"⚠️ Over Time: {task.title}",
                        message=f"{get_user_display_name(ticket.assignee)} has exceeded the {assigned_mins}m budget.",
                        organization=task.organization,
                        link=f"/workspace/tasks?task={task.id}"
                    )

def _notify_time_based(task, title, reason, due_datetime=None):
    recipients = get_task_recipients(task, include_creator=True)
    link = f"/tasks/{task.id}"
    
    for recipient in recipients:
        recipient_name = get_user_display_name(recipient)
        if reason == "overdue":
            message = f"Hello {recipient_name}, the task '{task.title}' is now overdue."
            n_type = "task_overdue"
        else:
            time_str = due_datetime.strftime('%I:%M %p, %b %d') if due_datetime else ""
            message = f"Hello {recipient_name}, reminder: the task '{task.title}' is due soon at {time_str}."
            n_type = "task_due_soon"
            
        NotificationService.send_notification(
            recipient=recipient,
            n_type=n_type,
            title=title,
            message=message,
            link=link,
            organization=task.organization
        )

@receiver(post_save, sender=TaskComment)
def notify_comment_lifecycle(sender, instance, created, **kwargs):
    """
    Triggers notifications when a new comment is created or when a reply is posted.
    """
    if created:
        actor_name = get_user_display_name(instance.user)
        link = f"/tasks/{instance.task.id}"
        
        # 1. Threaded Reply Notification: Notify parent comment author
        if instance.parent and instance.parent.user != instance.user:
            parent_author = instance.parent.user
            message = f"Hello {get_user_display_name(parent_author)}, {actor_name} replied to your comment on task '{instance.task.title}'."
            NotificationService.send_notification(
                recipient=parent_author,
                n_type="comment_reply",
                title="New reply to your comment",
                message=message,
                link=link,
                organization=instance.task.organization
            )
            
        # 2. General Comment Notification: Notify task assignees/watchers/creator
        recipients = get_task_recipients(instance.task, include_creator=True)
        for recipient in recipients:
            # Skip if recipient is comment author or the parent comment author (already notified)
            if recipient == instance.user:
                continue
            if instance.parent and recipient == instance.parent.user:
                continue
                
            message = f"Hello {get_user_display_name(recipient)}, {actor_name} commented on task '{instance.task.title}'."
            NotificationService.send_notification(
                recipient=recipient,
                n_type="task_comment",
                title="New Task Comment",
                message=message,
                link=link,
                organization=instance.task.organization
            )

@receiver(m2m_changed, sender=TaskComment.mentions.through)
def notify_comment_mentions(sender, instance, action, pk_set, **kwargs):
    """
    Triggers notifications to users when they are @mentioned in a task comment.
    """
    if action == "post_add":
        from django.contrib.auth import get_user_model
        User = get_user_model()
        mentioned_users = User.objects.filter(id__in=pk_set)
        
        actor_name = get_user_display_name(instance.user)
        title = "You were mentioned in a comment"
        link = f"/tasks/{instance.task.id}"
        
        for user in mentioned_users:
            if user == instance.user:
                continue  # Skip notifying self if self-mentioned
            
            message = f"Hello {get_user_display_name(user)}, {actor_name} mentioned you in a comment on task '{instance.task.title}'."
            NotificationService.send_notification(
                recipient=user,
                n_type="comment_mention",
                title=title,
                message=message,
                link=link,
                organization=instance.task.organization
            )

from tasks.models import TaskExtensionRequest

@receiver(post_save, sender=TaskExtensionRequest)
def handle_extension_request_notifications(sender, instance, created, **kwargs):
    """
    Trigger notifications when an extension is requested or reviewed.
    """
    task = instance.task
    link = f"/tasks/{task.id}"
    
    if created:
        # Send to Organization Owner/Admins
        from organizations.models import OrganizationMembership
        admins = OrganizationMembership.objects.filter(
            organization=task.organization, 
            role__in=['admin', 'owner'],
            is_active=True
        ).select_related('user')
        
        actor_name = get_user_display_name(instance.requested_by)
        for membership in admins:
            admin_user = membership.user
            NotificationService.send_notification(
                recipient=admin_user,
                n_type="extension_requested",
                title="Task Extension Requested",
                message=f"Hello {get_user_display_name(admin_user)}, {actor_name} requested an extension for task '{task.title}'.",
                link=link,
                organization=task.organization
            )
    else:
        # If the status changed from pending
        if instance.status != 'pending':
            recipient = instance.requested_by
            reviewer_name = get_user_display_name(instance.reviewed_by)
            
            if instance.status == 'approved':
                title = "Extension Approved"
                message = f"Hello {get_user_display_name(recipient)}, your extension request for '{task.title}' was approved by {reviewer_name}."
            elif instance.status == 'rejected':
                title = "Extension Rejected"
                message = f"Hello {get_user_display_name(recipient)}, your extension request for '{task.title}' was rejected by {reviewer_name}."
            elif instance.status == 'modified':
                title = "Extension Modified"
                message = f"Hello {get_user_display_name(recipient)}, your extension request for '{task.title}' was modified and approved by {reviewer_name}."
                
            NotificationService.send_notification(
                recipient=recipient,
                n_type="extension_reviewed",
                title=title,
                message=message,
                link=link,
                organization=task.organization
            )

@receiver(post_save, sender=Task)
def create_task_chat_room(sender, instance, created, **kwargs):
    if created:
        room, _ = ChatRoom.objects.get_or_create(
            organization=instance.organization,
            room_type='task',
            task=instance,
            defaults={'name': f"Task: {instance.title}"}
        )
    else:
        # Update name if task title changes
        ChatRoom.objects.filter(task=instance).update(name=f"Task: {instance.title}")

# Removed chat participant sync for many-to-many assignees; chat participants will be managed differently.


@receiver(post_save, sender=Task)
def sync_task_ticket(sender, instance, created, **kwargs):
    if instance.is_deleted:
        return
    if getattr(instance, '_skip_ticket_sync', False):
        return
    from tasks.models import TaskTicket
    if instance.assignee:
        ticket, ticket_created = TaskTicket.objects.get_or_create(
            task=instance,
            assignee=instance.assignee,
            defaults={'status': instance.status}
        )
        if not ticket_created and ticket.status != instance.status:
            ticket.status = instance.status
            ticket.save()
        TaskTicket.objects.filter(task=instance).exclude(assignee=instance.assignee).delete()
    else:
        TaskTicket.objects.filter(task=instance).delete()


from users.models import LeaveRequest

@receiver(post_save, sender=LeaveRequest)
def handle_leave_approved(sender, instance, created, **kwargs):
    """
    Whenever a leave request is approved, trigger rescheduling for the employee.
    """
    if instance.status == 'Approved' and instance.organization_id:
        from tasks.services.scheduler import reschedule_assignee_tasks
        reschedule_assignee_tasks(instance.user_id, instance.organization_id)

@receiver(post_save, sender=Task)
def sync_parent_task_status_on_subtask_save(sender, instance, created, **kwargs):
    if instance.parent_id:
        parent = instance.parent
        subtasks = parent.subtasks.all()
        if not subtasks.exists(): return
        statuses = set(subtasks.values_list('status', flat=True))
        new_status = 'todo'
        if len(statuses) == 1: new_status = statuses.pop()
        elif 'testing' in statuses: new_status = 'testing'
        elif 'in_review' in statuses: new_status = 'in_review'
        elif 'in_progress' in statuses: new_status = 'in_progress'
        if parent.status != new_status:
            parent.status = new_status
            parent.save(update_fields=['status'])
