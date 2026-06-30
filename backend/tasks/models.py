from django.db import models
from django.conf import settings
import uuid
from django.utils import timezone

class Task(models.Model):
    TYPE_CHOICES = [('task', 'Task'), ('story', 'Story'), ('bug', 'Bug')]
    STATUS_CHOICES = [
        ('backlog', 'Backlog'),
        ('todo', 'To Do'), 
        ('in_progress', 'In Progress'), 
        ('paused', 'Paused'),
        ('delayed', 'Delayed'),
        ('in_review', 'In Review'), 
        ('testing', 'Testing'), 
        ('done', 'Done')
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'), 
        ('medium', 'Medium'), 
        ('high', 'High')
    ]
    REMINDER_CHOICES = [
        ('none', 'No Reminder'),
        ('15m', '15 Minutes Before'),
        ('30m', '30 Minutes Before'),
        ('1h', '1 Hour Before'),
        ('2h', '2 Hours Before'),
        ('3h', '3 Hours Before'),
        ('1d', '1 Day Before'),
        ('custom', 'Custom Reminder'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    issue_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='task')
    goal = models.ForeignKey('goals.Goals', on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=500)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subtasks', help_text="Parent task if this is a split part")
    description = models.TextField(blank=True, null=True)
    # Each task is now assigned to a single user. A user can have many tasks.
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        help_text='The user responsible for this task (single assignee)'
    )
    watchers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='watched_tasks', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateTimeField(null=True, blank=True)
    due_time = models.TimeField(null=True, blank=True, help_text="Specific due time for minute-level precision")
    start_date = models.DateField(null=True, blank=True)
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    estimated_minutes = models.PositiveIntegerField(null=True, blank=True, help_text="Total estimated time in minutes")
    actual_time_spent_minutes = models.PositiveIntegerField(default=0, help_text="Total actual time spent in minutes")
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Actual time spent in hours")
    reminder_preference = models.CharField(max_length=10, choices=REMINDER_CHOICES, default='none')
    reminder_duration_minutes = models.PositiveIntegerField(null=True, blank=True, help_text="Custom reminder time in minutes before the due date")
    is_overdue = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(default=False)
    
    # Scheduling System Fields
    SCHEDULE_STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('QUEUED', 'Queued'),
        ('COMPLETED', 'Completed'),
    ]
    planned_start = models.DateTimeField(null=True, blank=True, help_text="Calculated planned start time")
    planned_end = models.DateTimeField(null=True, blank=True, help_text="Calculated planned end time")
    schedule_status = models.CharField(max_length=20, choices=SCHEDULE_STATUS_CHOICES, default='QUEUED')
    queue_position = models.PositiveIntegerField(null=True, blank=True, help_text="Position in the Queue Bucket")
    is_auto_scheduled = models.BooleanField(default=True, help_text="Whether this task was auto-scheduled")
    schedule_reason = models.TextField(blank=True, null=True, help_text="Reason for the current schedule status (e.g. no slots)")
    last_scheduler_run = models.DateTimeField(null=True, blank=True, help_text="When the scheduler last processed this task")

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_tasks')
    is_deleted = models.BooleanField(default=False)
    assigned_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Visibility Control
    VISIBILITY_CHOICES = [('organization', 'Entire Organization'), ('specific', 'Specific Users')]
    visibility_type = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='specific')
    visible_to = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='visible_tasks', blank=True)

    # Sharing System Fields
    shared_viewers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='shared_view_tasks', blank=True)
    sharing_option = models.CharField(max_length=20, choices=[
        ('private', 'Private'),
        ('organization', 'Entire Organization'),
        ('specific', 'Specific People')
    ], default='specific')

    # Extension Tracking
    extension_count = models.PositiveIntegerField(default=0, help_text="Number of extensions granted for this task")
    is_blocked = models.BooleanField(default=False, help_text="Task is blocked from further work or extensions")

    # Scoring-related fields
    impact = models.PositiveIntegerField(default=5, help_text="Impact score of the task (1-10)")

    RISK_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    risk = models.CharField(
        max_length=10,
        choices=RISK_CHOICES,
        default='medium',
        help_text="Risk level of the task: low=1, medium=2, high=3"
    )

    required_assignees = models.PositiveIntegerField(
        default=1,
        help_text="Number of required assignees for this task (1 for individual task, > 1 for group task)"
    )

    def calculate_score(self):
        """
        Calculate and return the Task Score.
        """
        # Fallback to a default score based on priority when calculations is commented out
        priority_map = {'low': 10.0, 'medium': 20.0, 'high': 30.0, 'urgent': 40.0}
        return priority_map.get(str(self.priority).lower(), 20.0)

    @property
    def assignees(self):
        """
        Backward compatibility helper returning a queryset of the single assignee (or empty).
        Allows methods like task.assignees.all() and task.assignees.exists() to work.
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if self.assignee_id:
            return User.objects.filter(id=self.assignee_id)
        return User.objects.none()
    @property
    def total_estimated_minutes(self) -> int:
        """
        Return the total estimated time in minutes.
        If estimated_minutes is set, use it (as it holds the total).
        Otherwise fallback to estimated_hours.
        """
        if self.estimated_minutes:
            return int(self.estimated_minutes)
        if self.estimated_hours:
            return int(round(float(self.estimated_hours) * 60))
        return 60

    class Meta:
        db_table = 'accounts_task'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['assignee', 'schedule_status', 'planned_start', 'planned_end'], name='task_sched_lookup_idx'),
        ]

    def __str__(self):
        return self.title

    def soft_delete(self):
        self.is_deleted = True
        self.save()

    def restore(self):
        self.is_deleted = False
        self.save()

class TaskComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    comment = models.TextField()
    mentions = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='task_comment_mentions')
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_taskcomment'
        ordering = ['created_at']  # Threaded lists are cleaner when sorted chronologically

    def soft_delete(self):
        self.is_deleted = True
        self.save()

class TaskAttachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    comment = models.ForeignKey(TaskComment, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    file = models.FileField(upload_to='task_attachments/%Y/%m/%d/')
    file_name = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'accounts_taskattachment'

    def __str__(self):
        return f"{self.file_name} on {self.task.title}"


class TaskTicket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='tickets')
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='task_tickets')
    status = models.CharField(max_length=20, choices=Task.STATUS_CHOICES, default='todo')
    time_spent_minutes = models.PositiveIntegerField(default=0, help_text="Total minutes spent on this ticket")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_taskticket'
        unique_together = ('task', 'assignee')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.task.title} - {self.assignee.email}"


class TaskExtensionRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('modified', 'Modified & Approved'),
    ]
    REASON_CHOICES = [
        ('more_time', 'Need More Time'),
        ('blocked', 'Blocked by Dependency'),
        ('scope_change', 'Scope Change'),
        ('personal', 'Personal / Sick Leave'),
        ('other', 'Other')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='extension_requests')
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='requested_extensions')
    reason_type = models.CharField(max_length=20, choices=REASON_CHOICES)
    reason_text = models.TextField(blank=True, null=True)
    proposed_date = models.DateTimeField(help_text="The new requested due date")
    requested_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Extra hours requested")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    manager_comment = models.TextField(blank=True, null=True, help_text="Reason for rejection or modification")
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_extensions')
    reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_taskextensionrequest'
        ordering = ['-created_at']

    def __str__(self):
        return f"Extension for {self.task.title} by {self.requested_by.email}"


class TaskFeedback(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='feedbacks')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='task_feedbacks')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    comments = models.TextField(blank=True, null=True, help_text="What problems did you face? What helped you complete it?")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'accounts_taskfeedback'
        ordering = ['-created_at']
        # One feedback per user per task
        unique_together = ('task', 'user')

    def __str__(self):
        return f"Feedback for {self.task.title} by {self.user.email}"


from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

# Duplicated signal handlers sync_task_ticket_single and sync_task_status_to_tickets removed.
# Task-to-ticket status and assignee syncing is handled by sync_task_ticket in signals.py.


def get_overall_task_status(task):
    """
    Intelligently calculate the overall master task status based on its tickets.
    Logic rules (similar to ClickUp/Jira):
    - If no tickets, keep current status.
    - If ALL tickets are 'done', master is 'done'.
    - If ANY ticket is 'testing', master is 'testing'.
    - If ANY ticket is 'in_review', master is 'in_review'.
    - If ANY ticket is 'in_progress', master is 'in_progress'.
    - If ALL tickets are 'todo' or 'backlog', master is 'todo'.
    """
    tickets = task.tickets.all()
    if not tickets.exists():
        return task.status
        
    statuses = set(tickets.values_list('status', flat=True))
    
    if len(statuses) == 1:
        return statuses.pop()
        
    if 'testing' in statuses:
        return 'testing'
    if 'in_review' in statuses:
        return 'in_review'
    if 'in_progress' in statuses:
        return 'in_progress'
    if 'todo' in statuses:
        return 'todo'
        
    return 'todo'


@receiver(post_save, sender=TaskTicket)
def sync_ticket_status_to_task(sender, instance, created, **kwargs):
    """
    When an individual TaskTicket changes status, intelligently recalculate the master Task status.
    """
    task = instance.task
    
    # Calculate what the master status should be
    new_status = get_overall_task_status(task)
    
    # If it needs to change, update it and skip propagating back down to tickets
    if task.status != new_status:
        task.status = new_status
        task._skip_ticket_sync = True
        task.save(update_fields=['status'])



class TaskSubmission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='submissions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='task_submissions')
    comments = models.TextField(blank=True, help_text="Description of the work done.")
    file_attachment = models.FileField(upload_to='task_submissions/', null=True, blank=True)
    url_links = models.TextField(blank=True, help_text="Comma-separated or newline-separated URLs.")
    
    visibility = models.CharField(max_length=50, choices=[
        ('all', 'All Organization'),
        ('specific', 'Specific People'),
        ('assignee_admins', 'Only Assignee + Owner/Admin')
    ], default='all')
    
    # Store specific user IDs if 'specific' visibility is selected
    visible_to = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='visible_task_submissions', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_tasksubmission'
        ordering = ['-created_at']

    def __str__(self):
        return f"Submission by {self.user.email} for {self.task.title}"


@receiver(pre_save, sender=TaskTicket)
def save_elapsed_time_on_ticket_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_ticket = TaskTicket.objects.get(pk=instance.pk)
            # If the ticket status was 'in_progress', we commit the elapsed time before updated_at gets updated
            if old_ticket.status == 'in_progress':
                elapsed_seconds = (timezone.now() - old_ticket.updated_at).total_seconds()
                if elapsed_seconds > 2:  # log if active for more than 2 seconds
                    elapsed_minutes = int(round(elapsed_seconds / 60.0))
                    # If status is changing, or if elapsed minutes > 0
                    if old_ticket.status != instance.status and elapsed_minutes == 0:
                        elapsed_minutes = 1
                    instance.time_spent_minutes += elapsed_minutes
        except TaskTicket.DoesNotExist:
            pass
