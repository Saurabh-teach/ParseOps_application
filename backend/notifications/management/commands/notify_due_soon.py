from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from tasks.models import Task
from goals.models import Goal
from notifications.services import NotificationService
from organizations.models import OrganizationMembership

class Command(BaseCommand):
    help = 'Send notifications for tasks due tomorrow and goals due in 2 days'

    def handle(self, *args, **options):
        today = timezone.localdate()
        
        # 1. Tasks Due Soon (1 day before due date, i.e. due tomorrow)
        tomorrow = today + timedelta(days=1)
        tasks_due_soon = Task.objects.filter(
            due_date=tomorrow,
            is_deleted=False
        ).exclude(status='done').select_related('assignee').prefetch_related('watchers')
        
        task_count = 0
        for task in tasks_due_soon:
            recipients = set()
            if task.assignee:
                recipients.add(task.assignee)
            for user in task.watchers.all():
                recipients.add(user)
                
            title = "Task Due Soon"
            message = f"Reminder: Task '{task.title}' is due tomorrow."
            link = f"/tasks/{task.id}"
            
            for recipient in recipients:
                NotificationService.send_notification(
                    recipient=recipient,
                    n_type="task_due_soon",
                    title=title,
                    message=message,
                    link=link,
                    organization=task.organization
                )
            task_count += 1
            
        self.stdout.write(self.style.SUCCESS(f"Notified for {task_count} tasks due soon."))

        # 2. Goals Due Soon (2 days before due date, i.e. due in 2 days)
        two_days_later = today + timedelta(days=2)
        goals_due_soon = Goal.objects.filter(
            due_date=two_days_later,
            is_deleted=False,
            is_active=True
        ).exclude(status='completed').select_related('owner', 'organization')
        
        goal_count = 0
        for goal in goals_due_soon:
            recipients = set()
            if goal.owner:
                recipients.add(goal.owner)
                
            # Get admins/owners of the organization
            managers = OrganizationMembership.objects.filter(
                organization=goal.organization,
                role__in=['admin', 'owner']
            ).select_related('user')
            
            for member in managers:
                if member.user:
                    recipients.add(member.user)
                    
            title = "Goal Due Soon"
            message = f"Reminder: Goal '{goal.title}' is due in 2 days."
            link = f"/goals/{goal.id}"
            
            for recipient in recipients:
                NotificationService.send_notification(
                    recipient=recipient,
                    n_type="goal_due_soon",
                    title=title,
                    message=message,
                    link=link,
                    organization=goal.organization
                )
            goal_count += 1
            
        self.stdout.write(self.style.SUCCESS(f"Notified for {goal_count} goals due soon."))
