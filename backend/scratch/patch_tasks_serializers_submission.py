import re

with open('c:/Users/saura/ParseOps/backend/tasks/serializers.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_serializer = """
from .models import TaskSubmission

class TaskSubmissionSerializer(serializers.ModelSerializer):
    user_details = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = TaskSubmission
        fields = ['id', 'task', 'user', 'user_details', 'comments', 'file_attachment', 'file_url', 'url_links', 'visibility', 'visible_to', 'created_at']
        read_only_fields = ['id', 'task', 'user', 'created_at']
        
    @extend_schema_field(serializers.JSONField())
    def get_user_details(self, obj):
        user = obj.user
        return {
            "id": str(user.id),
            "name": user.get_full_name() or user.email,
            "email": user.email,
            "initial": (user.first_name[0] if user.first_name else (user.email[0] if user.email else 'U')).upper()
        }

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file_attachment and hasattr(obj.file_attachment, 'url') and request is not None:
            return request.build_absolute_uri(obj.file_attachment.url)
        elif obj.file_attachment and hasattr(obj.file_attachment, 'url'):
            return obj.file_attachment.url
        return None
"""

content += new_serializer

# Add submissions to TaskDetailSerializer
target = "    tickets = TaskTicketSerializer(many=True, read_only=True)"
replacement = "    tickets = TaskTicketSerializer(many=True, read_only=True)\n    submissions = serializers.SerializerMethodField()"
content = content.replace(target, replacement)

target2 = "class Meta:"
replacement2 = """    @extend_schema_field(TaskSubmissionSerializer(many=True))
    def get_submissions(self, obj):
        request = self.context.get('request')
        if not request:
            return []
        
        user = request.user
        organization = obj.organization
        from organizations.models import OrganizationMembership
        membership = OrganizationMembership.objects.filter(organization=organization, user=user).first()
        if not membership:
            return []
            
        role = membership.role
        submissions = obj.submissions.all()
        
        filtered = []
        for s in submissions:
            # If owner/admin, or the creator of the submission
            if role in ['owner', 'admin'] or s.user == user:
                filtered.append(s)
            elif s.visibility == 'all':
                filtered.append(s)
            elif s.visibility == 'specific' and user in s.visible_to.all():
                filtered.append(s)
            elif s.visibility == 'assignee_admins' and user in obj.assignees.all():
                filtered.append(s)
                
        return TaskSubmissionSerializer(filtered, many=True, context={'request': request}).data

    class Meta:"""
content = content.replace(target2, replacement2, 1)

with open('c:/Users/saura/ParseOps/backend/tasks/serializers.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Added TaskSubmissionSerializer to tasks/serializers.py")
