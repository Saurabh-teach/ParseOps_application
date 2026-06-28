from rest_framework import serializers
from django.contrib.auth import get_user_model
from goals.models import Goals, KeyResult
from users.serializers import UserSerializer

User = get_user_model()

class KeyResultSerializer(serializers.ModelSerializer):
    progress = serializers.FloatField(read_only=True)

    class Meta:
        model = KeyResult
        fields = ['id', 'goal', 'title', 'target_value', 'current_value', 'unit', 'progress', 'created_at', 'updated_at']
        read_only_fields = ['id', 'progress', 'created_at', 'updated_at']

class GoalListSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    kr_count = serializers.IntegerField(source='key_results.count', read_only=True)
    parent_title = serializers.CharField(source='parent.title', read_only=True)
    depends_on_title = serializers.CharField(source='depends_on.title', read_only=True)
    computed_progress = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()
    done_task_count = serializers.SerializerMethodField()

    def get_computed_progress(self, obj):
        """
        Always compute progress in real-time:
        - If KRs exist: average of KR progress values
        - Else: task-based completion rate (done tasks / total tasks)
        """
        krs = obj.key_results.all()
        if krs.exists():
            total = sum(kr.progress for kr in krs)
            return round(total / krs.count(), 2)
        # Fall back to task-based progress
        linked_tasks = obj.tasks.filter(is_deleted=False)
        total_tasks = linked_tasks.count()
        if total_tasks > 0:
            done = linked_tasks.filter(status='done').count()
            return round((done / total_tasks) * 100, 2)
        return float(obj.progress)

    def get_task_count(self, obj):
        return obj.tasks.filter(is_deleted=False).count()

    def get_done_task_count(self, obj):
        return obj.tasks.filter(is_deleted=False, status='done').count()

    chat_room_id = serializers.SerializerMethodField()
    def get_chat_room_id(self, obj):
        if hasattr(obj, 'chat_room'):
            return str(obj.chat_room.id)
        return None

    class Meta:
        model = Goals
        fields = [
            'id', 'title', 'description', 
            'progress', 'computed_progress', 'status', 'priority', 'start_date', 'due_date', 'visibility_type',
            'owner', 'owner_email', 'created_by', 'created_by_email',
            'kr_count', 'task_count', 'done_task_count', 'created_at', 'updated_at',
            'parent', 'parent_title', 'depends_on', 'depends_on_title',
            'is_shared_externally',
            'assignees', 'shared_viewers', 'sharing_option', 'chat_room_id'
        ]

class GoalDetailSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    visible_to = UserSerializer(many=True, read_only=True)
    assignees = UserSerializer(many=True, read_only=True)
    shared_viewers = UserSerializer(many=True, read_only=True)
    key_results = KeyResultSerializer(many=True, read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    parent_title = serializers.CharField(source='parent.title', read_only=True)
    depends_on_title = serializers.CharField(source='depends_on.title', read_only=True)
    chat_room_id = serializers.SerializerMethodField()

    def get_chat_room_id(self, obj):
        if hasattr(obj, 'chat_room'):
            return str(obj.chat_room.id)
        return None

    class Meta:
        model = Goals
        fields = [
            'id', 'title', 'description', 'organization', 'organization_name',
            'owner', 'created_by', 'progress', 'status', 'priority', 'start_date', 'due_date', 'visibility_type', 'visible_to',
            'key_results', 'is_active', 'is_deleted', 'created_at', 'updated_at',
            'parent', 'parent_title', 'depends_on', 'depends_on_title',
            'is_shared_externally',
            'assignees', 'shared_viewers', 'sharing_option', 'chat_room_id'
        ]

class GoalCreateUpdateSerializer(serializers.ModelSerializer):
    assignees = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), required=False)
    shared_viewers = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), required=False)

    class Meta:
        model = Goals
        fields = [
            'id', 'title', 'description', 
            'progress', 'status', 'priority', 'start_date', 'due_date', 'timeframe', 'template_type', 'visible_to',
            'parent', 'depends_on', 'is_shared_externally',
            'assignees', 'shared_viewers', 'sharing_option'
        ]

    def validate(self, attrs):
        title = attrs.get('title')
        if title:
            request = self.context.get('request')
            if request and hasattr(request, 'parser_context'):
                view = request.parser_context.get('view')
                org = None
                if hasattr(view, 'get_organization'):
                    org = view.get_organization()
                elif hasattr(view, 'kwargs') and 'org_id' in view.kwargs:
                    from organizations.models import Organization
                    org_id = view.kwargs.get('org_id')
                    org = Organization.objects.filter(id=org_id).first()
                elif hasattr(view, 'request') and view.request.query_params.get('organization'):
                    from organizations.models import Organization
                    org_id = view.request.query_params.get('organization')
                    org = Organization.objects.filter(id=org_id).first()
                elif self.instance:
                    org = self.instance.organization

                if org:
                    from goals.models import Goals
                    qs = Goals.objects.filter(organization=org, title__iexact=title, is_deleted=False)
                    if self.instance:
                        qs = qs.exclude(id=self.instance.id)
                    if qs.exists():
                        raise serializers.ValidationError({"title": "A goal with this name already exists in this organization."})
        return attrs
