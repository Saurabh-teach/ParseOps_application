import uuid
from django.db import models
from django.conf import settings

class Note(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='notes',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=255, blank=True, default='')
    content = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'user_note'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.email} - {self.title or 'Untitled Note'}"
