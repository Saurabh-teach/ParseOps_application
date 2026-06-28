from django.contrib import admin
from .models import User, OTPVerification, PasswordResetToken

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'phone', 'city', 'job_title', 'department', 'is_staff', 'is_active', 'created_at')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'department')
    search_fields = ('email', 'phone', 'city', 'job_title', 'department')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('id', 'email', 'password')}),
        ('Personal Info', {'fields': ('phone', 'city', 'date_of_birth', 'job_title', 'department', 'profile_picture', 'bio')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )

@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ('phone', 'otp', 'purpose', 'expires_at', 'attempts', 'created_at')
    list_filter = ('purpose', 'expires_at')
    search_fields = ('phone', 'otp')
    ordering = ('-created_at',)

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'otp', 'is_used', 'expires_at', 'created_at')
    list_filter = ('is_used', 'expires_at')
    search_fields = ('user__email', 'token', 'otp')
    ordering = ('-created_at',)

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
