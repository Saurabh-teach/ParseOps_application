from rest_framework import serializers
from .models import DashboardApp, WorkspaceApp

class DashboardAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardApp
        fields = '__all__'

class WorkspaceAppSerializer(serializers.ModelSerializer):
    app_details = DashboardAppSerializer(source='app', read_only=True)
    
    class Meta:
        model = WorkspaceApp
        fields = ['id', 'app', 'app_details', 'is_enabled', 'settings', 'installed_at']
