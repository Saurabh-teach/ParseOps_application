import uuid
from django.db import models
from django.conf import settings
from organizations.models import Organization

class ProjectTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='templates')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_templates')
    
    VISIBILITY_CHOICES = (
        ('public', 'Organization Public'),
        ('private', 'Personal'),
    )
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.organization.name})"

class TemplateFolder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(ProjectTemplate, on_delete=models.CASCADE, related_name='folders')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)
    goal_title = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.name} - {self.template.name}"

class TemplateItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    folder = models.ForeignKey(TemplateFolder, on_delete=models.CASCADE, related_name='items')
    
    ITEM_TYPES = (
        ('document', 'Rich Text Document'),
        ('checklist', 'Checklist'),
        ('task_list', 'Sub-Task List'),
        ('file', 'File Upload'),
        ('link', 'URL/Link'),
        ('task', 'Standard Task'),
    )
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES)
    name = models.CharField(max_length=255)
    
    # Store dynamic content like JSON for checklists/tasks, or HTML/Markdown for docs
    content = models.JSONField(blank=True, null=True, default=dict)
    
    # Store file paths or URLs for 'file' or 'link' types
    file_attachment = models.FileField(upload_to='template_files/%Y/%m/', blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    
    order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.name} ({self.get_item_type_display()})"

class GoalFolder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    goal = models.ForeignKey('goals.Goals', on_delete=models.CASCADE, related_name='folders')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')
    name = models.CharField(max_length=255)
    order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']

class GoalItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    folder = models.ForeignKey(GoalFolder, on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(max_length=20, choices=TemplateItem.ITEM_TYPES)
    name = models.CharField(max_length=255)
    content = models.JSONField(blank=True, null=True, default=dict)
    file_attachment = models.FileField(upload_to='goal_files/%Y/%m/', blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']
