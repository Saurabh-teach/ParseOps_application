import re

with open('c:/Users/saura/ParseOps/backend/tasks/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_model = """
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
"""

content += new_model

with open('c:/Users/saura/ParseOps/backend/tasks/models.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Added TaskSubmission to tasks/models.py")
