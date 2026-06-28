import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.exceptions import ValidationError

class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    logo = models.ImageField(upload_to='org_logos/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    
    # Multi-tenancy additions
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='owned_organizations',
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)
    
    is_public = models.BooleanField(default=True)
    onboarding_completed = models.BooleanField(default=False)
    
    # Scheduling Configuration Settings
    working_start_time = models.TimeField(default='10:00:00')
    working_end_time = models.TimeField(default='19:00:00')
    working_days = models.JSONField(
        default=list, 
        blank=True, 
        help_text="List of working days (0=Monday, 6=Sunday). Default: [0, 1, 2, 3, 4]"
    )
    lunch_break_start = models.TimeField(default='13:00:00')
    lunch_break_end = models.TimeField(default='14:00:00')
    tea_break_start = models.TimeField(default='17:00:00')
    tea_break_end = models.TimeField(default='17:30:00')
    additional_breaks = models.JSONField(
        default=list, 
        blank=True, 
        help_text="List of extra breaks, e.g., [{'start': '15:00:00', 'end': '15:15:00'}]"
    )
    maximum_scan_days = models.PositiveIntegerField(default=7)
    timezone = models.CharField(max_length=50, default='Asia/Kolkata')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_organizations'
    )

    class Meta:
        db_table = 'org_table'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.working_days:
            self.working_days = [0, 1, 2, 3, 4] # Default Mon-Fri
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class OrganizationMembership(models.Model):
    ROLE_CHOICES = (
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    custom_permissions = models.JSONField(default=dict, blank=True)
    
    joined_at = models.DateTimeField(auto_now_add=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='invited_memberships'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'org_membership'
        unique_together = ('organization', 'user')

    def clean(self):
        super().clean()
        if not self._state.adding:
            try:
                old = OrganizationMembership.objects.get(pk=self.pk)
                # If demoting from owner or deactivating an owner
                if old.role == 'owner' and old.is_active:
                    if self.role != 'owner' or not self.is_active:
                        owner_count = OrganizationMembership.objects.filter(
                            organization=self.organization, 
                            role='owner', 
                            is_active=True
                        ).exclude(pk=self.pk).count()
                        if owner_count == 0:
                            raise ValidationError("An organization must have at least one active owner.")
            except OrganizationMembership.DoesNotExist:
                pass

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.role == 'owner' and self.is_active:
            owner_count = OrganizationMembership.objects.filter(
                organization=self.organization, 
                role='owner', 
                is_active=True
            ).exclude(pk=self.pk).count()
            if owner_count == 0:
                raise ValidationError("Cannot delete the last active owner of an organization.")
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} in {self.organization.name} ({self.role})"

class OrganizationJoinRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    ROLE_REQUEST_CHOICES = (
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('owner', 'Owner')
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='join_requests')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='join_requests')
    requested_role = models.CharField(max_length=20, choices=ROLE_REQUEST_CHOICES, default='member')
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='reviewed_requests'
    )

    class Meta:
        db_table = 'org_join_request'
        unique_together = ('organization', 'user', 'status')

    def __str__(self):
        return f"{self.user.email} -> {self.organization.name} ({self.status})"

class OrganizationInvitation(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='invitations')
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=OrganizationMembership.ROLE_CHOICES, default='member')
    token = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True, null=True)
    
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_invitations')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'org_invitation'

    def __str__(self):
        return f"Invite to {self.email} for {self.organization.name}"

# Abstract Scoped Model for Every Future Model (Task, Project, Document, Folder, etc.)
class OrganizationScopedModel(models.Model):
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name="%(class)ss"
    )

    class Meta:
        abstract = True

# Backward compatibility aliases to prevent breaking other files during migration
Membership = OrganizationMembership
Invitation = OrganizationInvitation
JoinRequest = OrganizationJoinRequest


# class SAMLConfiguration(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     company_name = models.CharField(max_length=255)
#     entity_id = models.CharField(max_length=255, help_text="IdP Entity ID / Issuer URL")
#     sso_url = models.URLField(help_text="Single Sign-On IdP URL")
#     x509_certificate = models.TextField(help_text="PEM public key certificate of IdP")
#     logout_url = models.URLField(null=True, blank=True, help_text="Optional logout URL")
#     is_active = models.BooleanField(default=True)
#     organization = models.ForeignKey(
#         Organization, 
#         on_delete=models.CASCADE, 
#         related_name='saml_configs',
#         null=True,
#         blank=True
#     )
#     
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
# 
#     class Meta:
#         db_table = 'saml_configuration'
#         ordering = ['company_name']
# 
#     def __str__(self):
#         return f"{self.company_name} ({self.entity_id})"

