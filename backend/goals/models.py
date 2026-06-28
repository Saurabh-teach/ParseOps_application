from django.db import models
from django.conf import settings
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
import uuid
from django.conf import settings
import uuid

class Goals(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_goals')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_goals')
    progress = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=[('not_started', 'Not Started'), ('in_progress', 'In Progress'), ('at_risk', 'At Risk'), ('completed', 'Completed')], default='not_started')
    priority = models.CharField(max_length=20, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='medium')
    start_date = models.DateField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Visibility Control
    VISIBILITY_CHOICES = [('organization', 'Entire Organization'), ('specific', 'Specific Users')]
    visibility_type = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='specific')
    visible_to = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='visible_goals', blank=True)

    # Sharing System Fields
    assignees = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='assigned_goals', blank=True)
    shared_viewers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='shared_view_goals', blank=True)
    sharing_option = models.CharField(max_length=20, choices=[
        ('private', 'Private'),
        ('organization', 'Entire Organization'),
        ('specific', 'Specific People')
    ], default='specific')

    # New Premium Goal Fields
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_goals')
    depends_on = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='dependent_goals')
    is_shared_externally = models.BooleanField(default=False)
    timeframe = models.CharField(max_length=20, default='quarterly')
    template_type = models.CharField(max_length=50, default='none')

    class Meta:
        db_table = 'accounts_goal'
        unique_together = ('title', 'organization')
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def soft_delete(self):
        self.is_deleted = True
        self.save()

    def restore(self):
        self.is_deleted = False
        self.save()

    def update_progress_from_krs(self):
        """
        Recalculates progress based on associated Key Results.
        If no KRs exist, falls back to task-based completion rate.
        """
        krs = self.key_results.all()
        if krs.exists():
            total_progress = sum(kr.progress for kr in krs)
            self.progress = round(total_progress / krs.count(), 2)
        else:
            # Fallback: compute progress from linked tasks
            linked_tasks = self.tasks.filter(is_deleted=False)
            total_tasks = linked_tasks.count()
            if total_tasks > 0:
                done_tasks = linked_tasks.filter(status='done').count()
                self.progress = round((done_tasks / total_tasks) * 100, 2)
            else:
                self.progress = 0.00

        if self.progress >= 100:
            self.status = 'completed'
        elif self.progress > 0:
            self.status = 'in_progress'
        else:
            self.status = 'not_started'
        self.save(update_fields=['progress', 'status'])

class KeyResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    goal = models.ForeignKey(Goals, on_delete=models.CASCADE, related_name='key_results')
    title = models.CharField(max_length=255)
    target_value = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    current_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    unit = models.CharField(max_length=50, default='%')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def progress(self):
        """
        Calculates current progress percentage.
        """
        if self.target_value == 0:
            return 100.00 if self.current_value > 0 else 0.00
        progress_val = (self.current_value / self.target_value) * 100
        return min(max(float(progress_val), 0.0), 100.0)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.goal.update_progress_from_krs()

    def delete(self, *args, **kwargs):
        goal = self.goal
        super().delete(*args, **kwargs)
        goal.update_progress_from_krs()

    def __str__(self):
        return f"{self.title} ({self.progress}%)"

# Alias Goal to Goals to support singular imports
Goal = Goals

@receiver(post_save, sender=Goals)
def create_goal_chat_room(sender, instance, created, **kwargs):
    if created:
        from chat.models import ChatRoom
        room, _ = ChatRoom.objects.get_or_create(
            organization=instance.organization,
            room_type='goal',
            goal=instance,
            defaults={'name': f"Goal: {instance.title}"}
        )

@receiver(m2m_changed, sender=Goals.assignees.through)
def sync_goal_chat_participants(sender, instance, action, pk_set, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear']:
        from chat.models import ChatRoom, ChatParticipant
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
