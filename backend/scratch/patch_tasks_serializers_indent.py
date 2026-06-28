with open('c:/Users/saura/ParseOps/backend/tasks/serializers.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove the incorrectly placed get_submissions method (lines 18-48 roughly)
# and restore 'class Meta:'
new_lines = []
skip = False
for i, line in enumerate(lines):
    if line.strip() == '@extend_schema_field(TaskSubmissionSerializer(many=True))':
        skip = True
        continue
    if skip:
        if line.strip() == 'class Meta:':
            skip = False
            new_lines.append(line)
        continue
    new_lines.append(line)

content = "".join(new_lines)

target = """class TaskDetailSerializer(serializers.ModelSerializer):
    organization_slug = serializers.CharField(source='organization.slug', read_only=True)
    created_by = UserSerializer(read_only=True)
    assignees = UserSerializer(many=True, read_only=True)
    goal_details = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    attachments = TaskAttachmentSerializer(many=True, read_only=True)
    tickets = TaskTicketSerializer(many=True, read_only=True)
    submissions = serializers.SerializerMethodField()"""

replacement = """class TaskDetailSerializer(serializers.ModelSerializer):
    organization_slug = serializers.CharField(source='organization.slug', read_only=True)
    created_by = UserSerializer(read_only=True)
    assignees = UserSerializer(many=True, read_only=True)
    goal_details = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    attachments = TaskAttachmentSerializer(many=True, read_only=True)
    tickets = TaskTicketSerializer(many=True, read_only=True)
    submissions = serializers.SerializerMethodField()

    @extend_schema_field(TaskSubmissionSerializer(many=True))
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
                
        return TaskSubmissionSerializer(filtered, many=True, context={'request': request}).data"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/backend/tasks/serializers.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("tasks/serializers.py fixed")
