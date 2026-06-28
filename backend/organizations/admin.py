from django.contrib import admin
from .models import (
    Organization, 
    OrganizationMembership, 
    OrganizationJoinRequest, 
    OrganizationInvitation
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'owner', 'is_active', 'is_public', 'onboarding_completed', 'created_at')
    list_filter = ('is_active', 'is_public', 'onboarding_completed', 'created_at')
    search_fields = ('name', 'slug', 'owner__email', 'created_by__email')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ('organization', 'user', 'role', 'joined_at', 'invited_by', 'is_active')
    list_filter = ('role', 'is_active', 'joined_at')
    search_fields = ('organization__name', 'user__email', 'role', 'invited_by__email')
    ordering = ('-joined_at',)
    readonly_fields = ('id',)

@admin.register(OrganizationJoinRequest)
class OrganizationJoinRequestAdmin(admin.ModelAdmin):
    list_display = ('organization', 'user', 'requested_role', 'status', 'requested_at', 'reviewed_by', 'reviewed_at')
    list_filter = ('requested_role', 'status', 'requested_at', 'reviewed_at')
    search_fields = ('organization__name', 'user__email', 'message')
    ordering = ('-requested_at',)
    readonly_fields = ('id', 'requested_at')

@admin.register(OrganizationInvitation)
class OrganizationInvitationAdmin(admin.ModelAdmin):
    list_display = ('organization', 'email', 'role', 'token', 'status', 'invited_by', 'created_at', 'expires_at')
    list_filter = ('role', 'status', 'created_at', 'expires_at')
    search_fields = ('organization__name', 'email', 'token', 'invited_by__email')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at')

# --- Auto Register All Other Models ---
import os
from django.apps import apps
from django.contrib import admin

_app_name = os.path.basename(os.path.dirname(__file__))
try:
    _app = apps.get_app_config(_app_name)
    for _model in _app.get_models():
        try:
            class _DynamicModelAdmin(admin.ModelAdmin):
                list_display = [f.name for f in _model._meta.fields]
            admin.site.register(_model, _DynamicModelAdmin)
        except admin.sites.AlreadyRegistered:
            pass
except Exception:
    pass
