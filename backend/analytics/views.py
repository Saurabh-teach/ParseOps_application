from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

from organizations.models import Organization, OrganizationMembership
from analytics.services import get_personal_analytics, get_team_analytics

class DashboardAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get Dashboard Analytics",
        description="Returns user-wise or team-wise analytics based on the user's role in the organization.",
        responses={200: inline_serializer(
            name='AnalyticsResponse',
            fields={
                'role': serializers.CharField(),
                # personal fields
                'total_tasks': serializers.IntegerField(required=False),
                'completed_tasks': serializers.IntegerField(required=False),
                'overdue_tasks': serializers.IntegerField(required=False),
                'in_progress_tasks': serializers.IntegerField(required=False),
                'efficiency': serializers.IntegerField(required=False),
                'goals_involved': serializers.IntegerField(required=False),
                # team fields
                'overall_total_tasks': serializers.IntegerField(required=False),
                'overall_completed_tasks': serializers.IntegerField(required=False),
                'overall_efficiency': serializers.IntegerField(required=False),
                'total_goals': serializers.IntegerField(required=False),
                'member_stats': serializers.ListField(child=serializers.DictField(), required=False),
            }
        )}
    )
    def get(self, request, org_id):
        try:
            organization = Organization.objects.get(id=org_id)
            membership = OrganizationMembership.objects.get(organization=organization, user=request.user, is_active=True)
        except (Organization.DoesNotExist, OrganizationMembership.DoesNotExist):
            return Response({"error": "Organization not found or access denied.", "detail": "You are not an active member of this organization."}, status=403)
            
        role = membership.role
        
        # Role-Based Access Control logic for the dashboard
        if role in ['admin', 'owner']:
            data = get_team_analytics(organization, request.query_params, request.user)
            data['role'] = role # preserve exact role (admin or owner)
            return Response(data)
        else:
            # Normal member
            data = get_personal_analytics(request.user, organization, request.query_params)
            data['role'] = 'member'
            return Response(data)
