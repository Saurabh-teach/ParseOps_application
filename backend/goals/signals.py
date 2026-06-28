from django.db.models.signals import post_save, post_delete, pre_save, pre_delete
from django.dispatch import receiver
from django.db import transaction
from tasks.models import Task
from goals.models import Goal
from notifications.services import NotificationService
from organizations.models import OrganizationMembership

def notify_goal_created(goal_id):
    try:
        goal = Goal.objects.select_related('owner', 'organization').get(id=goal_id)
    except Goal.DoesNotExist:
        return
        
    recipients = set()
    if goal.owner:
        recipients.add(goal.owner)
        
    managers = OrganizationMembership.objects.filter(
        organization=goal.organization,
        role__in=['admin', 'owner']
    ).select_related('user')
    
    for member in managers:
        if member.user:
            recipients.add(member.user)
             
    title = "New Goal Created"
    message = f"Goal '{goal.title}' has been created in your organization."
    link = f"/goals/{goal.id}"
    
    for recipient in recipients:
        NotificationService.send_notification(
            recipient=recipient,
            n_type="goal_created",
            title=title,
            message=message,
            link=link
        )

def notify_goal_updated(goal_id):
    try:
        goal = Goal.objects.select_related('owner').get(id=goal_id)
    except Goal.DoesNotExist:
        return
        
    recipients = set()
    if goal.owner:
        recipients.add(goal.owner)
        
    linked_tasks = Task.objects.filter(goal=goal, is_deleted=False).select_related('assignee')
    for task in linked_tasks:
        if task.assignee:
            recipients.add(task.assignee)
            
    title = "Goal Updated"
    message = f"Goal '{goal.title}' has been updated."
    link = f"/goals/{goal.id}"
    
    for recipient in recipients:
        NotificationService.send_notification(
            recipient=recipient,
            n_type="goal_updated",
            title=title,
            message=message,
            link=link
        )

def notify_goal_completed(goal_id):
    try:
        goal = Goal.objects.select_related('owner').get(id=goal_id)
    except Goal.DoesNotExist:
        return
        
    recipients = set()
    if goal.owner:
        recipients.add(goal.owner)
        
    linked_tasks = Task.objects.filter(goal=goal, is_deleted=False).select_related('assignee')
    for task in linked_tasks:
        if task.assignee:
            recipients.add(task.assignee)
            
    title = "Goal Completed!"
    message = f"Congratulations! Goal '{goal.title}' has been marked as completed."
    link = f"/goals/{goal.id}"
    
    for recipient in recipients:
        NotificationService.send_notification(
            recipient=recipient,
            n_type="goal_completed",
            title=title,
            message=message,
            link=link
        )

def notify_goal_deleted_immediate(goal):
    recipients = set()
    if goal.owner:
        recipients.add(goal.owner)
        
    linked_tasks = Task.objects.filter(goal=goal, is_deleted=False).select_related('assignee')
    for task in linked_tasks:
        if task.assignee:
            recipients.add(task.assignee)
            
    title = "Goal Deleted"
    message = f"Goal '{goal.title}' has been deleted."
    
    for recipient in recipients:
        NotificationService.send_notification(
            recipient=recipient,
            n_type="goal_deleted",
            title=title,
            message=message,
            link=None
        )

@receiver(pre_save, sender=Goal)
def track_goal_changes(sender, instance, **kwargs):
    if instance.pk:
        try:
            orig = Goal.objects.get(pk=instance.pk)
            instance._old_status = orig.status
            instance._was_deleted = orig.is_deleted
            instance._user_facing_changed = (
                orig.title != instance.title or
                orig.description != instance.description or
                orig.priority != instance.priority
            )
        except Goal.DoesNotExist:
            instance._old_status = None
            instance._was_deleted = False
            instance._user_facing_changed = False
    else:
        instance._old_status = None
        instance._was_deleted = False
        instance._user_facing_changed = False

@receiver(post_save, sender=Goal)
def handle_goal_save(sender, instance, created, **kwargs):
    if created:
        transaction.on_commit(lambda: notify_goal_created(instance.id))
    else:
        was_deleted = getattr(instance, '_was_deleted', False)
        old_status = getattr(instance, '_old_status', None)
        user_facing_changed = getattr(instance, '_user_facing_changed', False)
        
        # Determine if this was a background progress update
        update_fields = kwargs.get('update_fields')
        is_only_progress = update_fields and set(update_fields).issubset({'progress', 'status'})
        
        if instance.is_deleted and not was_deleted:
            transaction.on_commit(lambda: notify_goal_deleted_immediate(instance))
        elif not instance.is_deleted:
            if instance.status == 'completed' and old_status != 'completed':
                transaction.on_commit(lambda: notify_goal_completed(instance.id))
            elif user_facing_changed and not is_only_progress:
                transaction.on_commit(lambda: notify_goal_updated(instance.id))

from django.db.models.signals import m2m_changed

@receiver(m2m_changed, sender=Goal.assignees.through)
def handle_goal_assignees_changed(sender, instance, action, pk_set, **kwargs):
    if action == "post_add" and pk_set:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        assigned_users = User.objects.filter(id__in=pk_set)
        title = "New Goal Assigned"
        link = f"/goals/{instance.id}"
        actor = getattr(instance, '_current_user', None)
        actor_name = actor.email if actor else "Someone"
        
        for user in assigned_users:
            message = f"Hello, you have been assigned to goal '{instance.title}' by {actor_name}."
            NotificationService.send_notification(
                recipient=user,
                n_type="goal_assigned",
                title=title,
                message=message,
                link=link,
                organization=instance.organization
            )


# ===== Task Status Change → Auto-Update Goal Progress =====

@receiver(pre_save, sender=Task)
def track_task_status_change(sender, instance, **kwargs):
    """Track task status before save so we can detect status changes."""
    if instance.pk:
        try:
            orig = Task.objects.get(pk=instance.pk)
            instance._old_task_status = orig.status
            instance._old_task_goal = orig.goal_id
        except Task.DoesNotExist:
            instance._old_task_status = None
            instance._old_task_goal = None
    else:
        instance._old_task_status = None
        instance._old_task_goal = None

@receiver(post_save, sender=Task)
def auto_update_goal_progress_on_task_save(sender, instance, created, **kwargs):
    """
    When a task status changes or is newly linked to a goal,
    auto-recalculate that goal's progress from task completion rate.
    """
    goal_ids_to_update = set()

    # Always update the goal the task is currently linked to
    if instance.goal_id:
        goal_ids_to_update.add(str(instance.goal_id))

    # Also update the old goal if the task was moved from a different goal
    old_goal_id = getattr(instance, '_old_task_goal', None)
    if old_goal_id and str(old_goal_id) != str(instance.goal_id):
        goal_ids_to_update.add(str(old_goal_id))

    # Only recalculate if status actually changed or task is new or goal changed
    old_status = getattr(instance, '_old_task_status', None)
    if not goal_ids_to_update:
        return
    if not created and old_status == instance.status and not getattr(instance, '_old_task_goal', None):
        return

    def _update_goals():
        for goal_id in goal_ids_to_update:
            try:
                goal = Goal.objects.get(id=goal_id)
                goal.update_progress_from_krs()
            except Goal.DoesNotExist:
                pass

    transaction.on_commit(_update_goals)

# ===== Goal Contextual Chat Room Sync =====

from chat.models import ChatRoom, ChatParticipant

@receiver(post_save, sender=Goal)
def create_goal_chat_room(sender, instance, created, **kwargs):
    if created:
        room, _ = ChatRoom.objects.get_or_create(
            organization=instance.organization,
            room_type='goal',
            goal=instance,
            defaults={'name': f"Goal: {instance.title}"}
        )
    else:
        ChatRoom.objects.filter(goal=instance).update(name=f"Goal: {instance.title}")

@receiver(m2m_changed, sender=Goal.assignees.through)
def sync_goal_chat_participants(sender, instance, action, pk_set, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear']:
        try:
            room = ChatRoom.objects.get(goal=instance, room_type='goal')
        except ChatRoom.DoesNotExist:
            room = ChatRoom.objects.create(
                organization=instance.organization,
                room_type='goal',
                goal=instance,
                name=f"Goal: {instance.title}"
            )
            
        if action == 'post_add' and pk_set:
            for user_id in pk_set:
                ChatParticipant.objects.get_or_create(room=room, user_id=user_id)
        elif action == 'post_remove' and pk_set:
            ChatParticipant.objects.filter(room=room, user_id__in=pk_set).delete()
        elif action == 'post_clear':
            ChatParticipant.objects.filter(room=room).delete()

@receiver(pre_delete, sender=Goal)
def handle_goal_pre_delete(sender, instance, **kwargs):
    if not instance.is_deleted:
        notify_goal_deleted_immediate(instance)
