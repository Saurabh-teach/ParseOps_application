from rest_framework import serializers
from django.utils import timezone
from tasks.models import Task, TaskComment, TaskAttachment, TaskTicket, TaskExtensionRequest, TaskFeedback
from users.models import User
from goals.models import Goals
from drf_spectacular.utils import extend_schema_field


def get_ticket_timer_data(ticket):
    running_elapsed_seconds = 0
    if ticket.status == 'in_progress' and ticket.updated_at:
        running_elapsed_seconds = max(0, int((timezone.now() - ticket.updated_at).total_seconds()))

    base_seconds = (ticket.time_spent_minutes or 0) * 60
    return {
        "time_spent_minutes": ticket.time_spent_minutes,
        "running_elapsed_seconds": running_elapsed_seconds,
        "total_elapsed_seconds": base_seconds + running_elapsed_seconds,
        "timer_started_at": ticket.updated_at.isoformat() if ticket.status == 'in_progress' and ticket.updated_at else None,
    }

class TaskCommentSerializer(serializers.ModelSerializer):
    """
    Serializer for Task Comments with threaded replies, @mentions, and attachments.
    """
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_avatar = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    mentions_details = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = TaskComment
        fields = [
            'id', 'task', 'user', 'user_id', 'user_name', 'user_email', 'user_avatar', 'parent', 'comment', 
            'mentions', 'mentions_details', 'is_edited', 'is_deleted', 'created_at', 'updated_at', 
            'replies', 'attachments'
        ]
        read_only_fields = [
            'id', 'task', 'user', 'user_id', 'user_name', 'user_email', 'user_avatar', 'is_edited', 'is_deleted', 
            'created_at', 'updated_at', 'replies', 'attachments'
        ]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_user_avatar(self, obj):
        if obj.user.profile_picture:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.user.profile_picture.url)
            return obj.user.profile_picture.url
        return None

    @extend_schema_field(serializers.ListField(child=serializers.JSONField()))
    def get_replies(self, obj):
        # Recursively serialize replies
        replies_qs = obj.replies.all().order_by('created_at')
        return TaskCommentSerializer(replies_qs, many=True, context=self.context).data

    @extend_schema_field(serializers.ListField(child=serializers.JSONField()))
    def get_mentions_details(self, obj):
        return [
            {
                "id": str(user.id), 
                "name": user.get_full_name() or user.email, 
                "email": user.email,
                "initial": (user.email[0] if user.email else 'U').upper()
            }
            for user in obj.mentions.all()
        ]

    @extend_schema_field(serializers.ListField(child=serializers.JSONField()))
    def get_attachments(self, obj):
        from tasks.serializers import TaskAttachmentSerializer
        return TaskAttachmentSerializer(obj.attachments.all(), many=True, context=self.context).data

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.is_deleted:
            rep['comment'] = "This comment was deleted."
        return rep


class CommentListSerializer(TaskCommentSerializer):
    """
    Explicit alias for listing task comments with replies.
    """
    pass


class CommentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a Task Comment or threaded reply.
    """
    attachment_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        write_only=True
    )

    class Meta:
        model = TaskComment
        fields = ['id', 'parent', 'comment', 'attachment_ids']

    def create(self, validated_data):
        attachment_ids = validated_data.pop('attachment_ids', [])
        comment = super().create(validated_data)
        if attachment_ids:
            TaskAttachment.objects.filter(id__in=attachment_ids, task=comment.task).update(comment=comment)
        return comment


class CommentUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating comment body text.
    """
    class Meta:
        model = TaskComment
        fields = ['comment']


class TaskAttachmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Task Attachments.
    """
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)

    class Meta:
        model = TaskAttachment
        fields = ['id', 'task', 'file', 'file_name', 'uploaded_by_name', 'uploaded_at']
        read_only_fields = ['id', 'file_name', 'uploaded_by_name', 'uploaded_at']


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for creating, updating, and listing Tasks.
    """
    assignee = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
    )
    assignees = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        required=False
    )
    watchers = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        many=True, 
        required=False
    )
    visible_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        many=True, 
        required=False
    )
    shared_viewers = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        required=False
    )
    assignee_details = serializers.SerializerMethodField()
    watcher_details = serializers.SerializerMethodField()
    shared_viewer_details = serializers.SerializerMethodField()
    completion_date = serializers.SerializerMethodField()
    goal_details = serializers.SerializerMethodField()
    creator_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    chat_room_id = serializers.SerializerMethodField()

    # Intelligent planning fields (read-only)
    days_needed = serializers.SerializerMethodField()
    suggested_due_date = serializers.SerializerMethodField()
    load_warnings = serializers.SerializerMethodField()
    segments = serializers.SerializerMethodField()
    
    # Post-Task Feedback (visible to admins/owners)
    feedbacks = serializers.SerializerMethodField()
    
    # Scoring-related fields
    task_score = serializers.SerializerMethodField()
    suggested_assignee_details = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'goal', 'organization', 'goal_details', 'issue_type', 'title', 'description', 
            'assignee', 'assignees', 'assignee_details', 'watchers', 'watcher_details', 'status', 'priority', 
            'due_date', 'due_time', 'start_date', 'estimated_hours', 'estimated_minutes', 
            'actual_hours', 'actual_time_spent_minutes', 'reminder_preference', 'reminder_duration_minutes', 
            'is_overdue', 'reminder_sent', 'visibility_type', 'visible_to',
            'created_by', 'creator_name', 'assigned_at', 'created_at', 'updated_at', 'completion_date',
            'days_needed', 'suggested_due_date', 'load_warnings',
            'shared_viewers', 'sharing_option', 'shared_viewer_details',
            'extension_count', 'is_blocked', 'feedbacks', 'chat_room_id',
            'impact', 'risk', 'task_score', 'suggested_assignee_details',
            'planned_start', 'planned_end', 'schedule_status', 'schedule_reason', 'is_auto_scheduled', 'segments'
        ]
        read_only_fields = [
            'id', 'organization', 'created_at', 'updated_at', 'created_by', 'assigned_at', 'is_overdue', 'reminder_sent',
            'days_needed', 'suggested_due_date', 'load_warnings', 'extension_count', 'is_blocked', 'chat_room_id',
            'task_score', 'schedule_status'
        ]

    def validate(self, attrs):
        # 0. Map assignees list to single assignee field
        if 'assignees' in attrs:
            assignees_list = attrs.pop('assignees')
            attrs['assignee'] = assignees_list[0] if assignees_list else None

        # 1. Sync estimated hours and minutes
        est_hours = attrs.get('estimated_hours')
        est_mins = attrs.get('estimated_minutes')
        
        if est_hours is not None and est_mins is None:
            attrs['estimated_minutes'] = int(float(est_hours) * 60)
        elif est_mins is not None and est_hours is None:
            attrs['estimated_hours'] = est_mins / 60.0

        # 2. Sync actual hours and minutes
        act_hours = attrs.get('actual_hours')
        act_mins = attrs.get('actual_time_spent_minutes')
        
        if act_hours is not None and act_mins is None:
            attrs['actual_time_spent_minutes'] = int(float(act_hours) * 60)
        elif act_mins is not None and act_hours is None:
            attrs['actual_hours'] = act_mins / 60.0

        # 3. Custom Reminder validations
        rem_pref = attrs.get('reminder_preference', getattr(self.instance, 'reminder_preference', 'none') if self.instance else 'none')
        rem_dur = attrs.get('reminder_duration_minutes', getattr(self.instance, 'reminder_duration_minutes', None) if self.instance else None)
        
        if rem_pref == 'custom' and rem_dur is None:
            raise serializers.ValidationError({
                "reminder_duration_minutes": "Custom reminder duration in minutes is required when reminder_preference is 'custom'."
            })

        # 4. Check if assignee is on leave during task period
        assignee = attrs.get('assignee', self.instance.assignee if self.instance else None)
            
        start_date = attrs.get('start_date', getattr(self.instance, 'start_date', None) if self.instance else None)
        due_date_dt = attrs.get('due_date', getattr(self.instance, 'due_date', None) if self.instance else None)
        
        from django.utils import timezone
        start_date_val = start_date or timezone.now().date()
        due_date_val = due_date_dt.date() if due_date_dt else None
        
        if assignee and due_date_val:
            from users.models import LeaveRequest
            overlapping_leaves = LeaveRequest.objects.filter(
                user=assignee,
                status='Approved',
                start_date__lte=due_date_val,
                end_date__gte=start_date_val
            )
            if overlapping_leaves.exists():
                user_name = f"{assignee.first_name} {assignee.last_name}".strip() or assignee.email
                raise serializers.ValidationError({
                    "assignees": f"{user_name} is on leave from {overlapping_leaves[0].start_date} to {overlapping_leaves[0].end_date}."
                })

        # 5. Only one task "in_progress" per assignee validation - REMOVED to allow multiple task assignments
        
        # 6. Check uniqueness of task name within the goal
        title = attrs.get('title', getattr(self.instance, 'title', None) if self.instance else None)
        goal = attrs.get('goal', getattr(self.instance, 'goal', None) if self.instance else None)
        if title and goal:
            qs = Task.objects.filter(goal=goal, title__iexact=title, is_deleted=False)
            if self.instance:
                qs = qs.exclude(id=self.instance.id)
            if qs.exists():
                raise serializers.ValidationError({"title": "A task with this name already exists in this goal."})

        return attrs

    @extend_schema_field(serializers.JSONField(allow_null=True))
    def get_goal_details(self, obj):
        if obj.goal:
            return {
                "id": str(obj.goal.id), 
                "title": obj.goal.title,
                "created_by_id": str(obj.goal.created_by_id) if obj.goal.created_by_id else None
            }
        return None

    @extend_schema_field(serializers.FloatField())
    def get_task_score(self, obj):
        # Commented: Smart Suggestion Feature
        return 0.0

    @extend_schema_field(serializers.ListField(child=serializers.JSONField()))
    def get_assignee_details(self, obj):
        # Commented: Smart Suggestion Feature
        # from tasks.calculations import calculate_final_assignment_score
        if obj.assignee:
            return [
                {
                    "id": str(obj.assignee.id), 
                    "name": obj.assignee.get_full_name() or obj.assignee.email, 
                    "email": obj.assignee.email,
                    "initial": (obj.assignee.email[0] if obj.assignee.email else 'U').upper(),
                    "employee_score": None,
                    "fatigue_score": None,
                    "match_score": None
                }
            ]
        return []

    @extend_schema_field(serializers.ListField(child=serializers.JSONField()))
    def get_watcher_details(self, obj):
        return [
            {
                "id": str(user.id), 
                "name": user.get_full_name() or user.email, 
                "email": user.email,
                "initial": (user.email[0] if user.email else 'U').upper()
            } 
            for user in obj.watchers.all()
        ]

    @extend_schema_field(serializers.ListField(child=serializers.JSONField()))
    def get_shared_viewer_details(self, obj):
        return [
            {
                "id": str(user.id), 
                "name": user.get_full_name() or user.email, 
                "email": user.email,
                "initial": (user.first_name[0] if user.first_name else (user.email[0] if user.email else 'U')).upper()
            } 
            for user in obj.shared_viewers.all()
        ]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_completion_date(self, obj):
        if obj.status == 'done':
            return obj.updated_at.strftime("%d %b %Y")
        return None

    @extend_schema_field(serializers.ListField(child=serializers.JSONField(), allow_null=True))
    def get_feedbacks(self, obj):
        request = self.context.get('request')
        if not request:
            return None
            
        from core.permissions import get_member_membership
        membership = get_member_membership(request, obj.organization_id)
        if membership and membership.role in ['admin', 'owner']:
            feedbacks = obj.feedbacks.all()
            return TaskFeedbackSerializer(feedbacks, many=True, context=self.context).data
        return None

    @extend_schema_field(serializers.FloatField())
    def get_days_needed(self, obj):
        from tasks.utils import calculate_days_needed
        hours = obj.total_estimated_minutes / 60.0
        return round(calculate_days_needed(hours), 2)

    @extend_schema_field(serializers.DateTimeField(allow_null=True))
    def get_suggested_due_date(self, obj):
        from tasks.utils import suggest_realistic_due_date
        hours = obj.total_estimated_minutes / 60.0
        if hours <= 0.0:
            return None
        start = obj.start_date
        user_id = obj.assignee_id
        
        return suggest_realistic_due_date(
            start_date=start,
            estimated_hours=hours,
            user_id=user_id,
            organization_id=obj.organization_id,
            exclude_task_id=obj.id
        )

    @extend_schema_field(serializers.JSONField(allow_null=True))
    def get_segments(self, obj):
        if obj.schedule_status == 'SCHEDULED' and obj.schedule_reason:
            import json
            try:
                # If the string starts with '[' it's a JSON list of segments
                if obj.schedule_reason.strip().startswith('['):
                    segs = json.loads(obj.schedule_reason)
                    from tasks.services.calendar import to_org_tz
                    from django.utils.dateparse import parse_datetime
                    for seg in segs:
                        if 'start' in seg:
                            dt_start = parse_datetime(seg['start'])
                            if dt_start:
                                seg['start'] = to_org_tz(dt_start, obj.organization).isoformat()
                        if 'end' in seg:
                            dt_end = parse_datetime(seg['end'])
                            if dt_end:
                                seg['end'] = to_org_tz(dt_end, obj.organization).isoformat()
                    return segs
            except Exception:
                pass
        return None

    @extend_schema_field(serializers.ListField(child=serializers.JSONField()))
    def get_load_warnings(self, obj):
        from tasks.utils import get_load_warnings
        if not obj.due_date:
            return []
        
        if obj.assignee:
            return get_load_warnings(
                user_id=obj.assignee.id,
                date=obj.due_date.date(),
                organization_id=obj.organization_id,
                exclude_task_id=obj.id
            )
        return []

    @extend_schema_field(serializers.UUIDField(allow_null=True))
    def get_chat_room_id(self, obj):
        if hasattr(obj, 'chat_room'):
            return obj.chat_room.id
        return None

    @extend_schema_field(serializers.JSONField(allow_null=True))
    def get_suggested_assignee_details(self, obj):
        return get_suggested_assignee_details_helper(obj, self.context)

    @extend_schema_field(serializers.JSONField(allow_null=True))
    def get_suggested_assignee(self, obj):
        return None

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        try:
            from tasks.services.calendar import to_org_tz
            if instance.planned_start:
                ret['planned_start'] = to_org_tz(instance.planned_start, instance.organization).isoformat()
            if instance.planned_end:
                ret['planned_end'] = to_org_tz(instance.planned_end, instance.organization).isoformat()
        except Exception:
            pass
        return ret

def get_suggested_assignee_details_helper(obj, context=None):
    return None


class TaskDetailSerializer(serializers.ModelSerializer):
    """
    Detailed Serializer for a Task, including comments and attachments.
    """
    comments = TaskCommentSerializer(many=True, read_only=True)
    attachments = TaskAttachmentSerializer(many=True, read_only=True)
    assignees = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)
    shared_viewers = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)
    assignee_details = serializers.SerializerMethodField()
    watcher_details = serializers.SerializerMethodField()
    shared_viewer_details = serializers.SerializerMethodField()
    creator_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    goal_details = serializers.SerializerMethodField()

    days_needed = serializers.SerializerMethodField()
    suggested_due_date = serializers.SerializerMethodField()
    load_warnings = serializers.SerializerMethodField()
    tickets = serializers.SerializerMethodField()
    feedbacks = serializers.SerializerMethodField()
    extension_requests = serializers.SerializerMethodField()
    chat_room_id = serializers.SerializerMethodField()
    
    # Scoring-related fields
    task_score = serializers.SerializerMethodField()
    suggested_assignee_details = serializers.SerializerMethodField()
    assignee_schedule = serializers.SerializerMethodField()
    segments = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'goal', 'goal_details', 'organization', 'issue_type', 'title', 'description', 
            'assignee', 'assignees', 'assignee_details', 'watchers', 'watcher_details', 'status', 'priority', 
            'due_date', 'due_time', 'start_date', 'estimated_hours', 'estimated_minutes', 
            'actual_hours', 'actual_time_spent_minutes', 'reminder_preference', 'reminder_duration_minutes', 
            'is_overdue', 'reminder_sent', 'comments', 'attachments', 'created_by', 'creator_name',
            'visibility_type', 'visible_to', 'created_at', 'updated_at',
            'days_needed', 'suggested_due_date', 'load_warnings',
            'shared_viewers', 'sharing_option', 'shared_viewer_details', 'tickets',
            'extension_count', 'is_blocked', 'feedbacks', 'extension_requests', 'chat_room_id',
            'impact', 'risk', 'task_score', 'suggested_assignee_details',
            'planned_start', 'planned_end', 'schedule_status', 'assignee_schedule', 'segments'
        ]
        read_only_fields = [
            'id', 'organization', 'created_at', 'updated_at', 'is_overdue', 'reminder_sent',
            'days_needed', 'suggested_due_date', 'load_warnings', 'tickets', 'chat_room_id',
            'task_score', 'planned_start', 'planned_end', 'schedule_status', 'assignee_schedule', 'segments'
        ]

    @extend_schema_field(serializers.JSONField(allow_null=True))
    def get_suggested_assignee_details(self, obj):
        return get_suggested_assignee_details_helper(obj, self.context)

    @extend_schema_field(serializers.JSONField(allow_null=True))
    def get_assignee_schedule(self, obj):
        """Returns the assignee's personal working schedule for frontend bidirectional sync."""
        if not obj.assignee:
            return None
        user = obj.assignee
        from users.models import UserWorkingSchedule
        schedule = UserWorkingSchedule.objects.filter(user=user).first()
        
        if schedule:
            return {
                'work_start_time': str(schedule.work_start_time) if schedule.work_start_time else '10:00:00',
                'work_end_time': str(schedule.work_end_time) if schedule.work_end_time else '19:00:00',
                'lunch_break_start': str(schedule.lunch_break_start) if schedule.lunch_break_start else '13:00:00',
                'lunch_break_end': str(schedule.lunch_break_end) if schedule.lunch_break_end else '14:00:00',
                'tea_break_start': str(schedule.tea_break_start) if schedule.tea_break_start else '17:00:00',
                'tea_break_end': str(schedule.tea_break_end) if schedule.tea_break_end else '17:30:00',
            }
        
        return {
            'work_start_time': '10:00:00',
            'work_end_time': '19:00:00',
            'lunch_break_start': '13:00:00',
            'lunch_break_end': '14:00:00',
            'tea_break_start': '17:00:00',
            'tea_break_end': '17:30:00',
        }

    @extend_schema_field(serializers.JSONField(allow_null=True))
    def get_goal_details(self, obj):
        if obj.goal:
            return {
                "id": str(obj.goal.id), 
                "title": obj.goal.title
            }
        return None

    @extend_schema_field(serializers.UUIDField(allow_null=True))
    def get_chat_room_id(self, obj):
        if hasattr(obj, 'chat_room'):
            return obj.chat_room.id
        return None

    @extend_schema_field(serializers.FloatField())
    def get_task_score(self, obj):
        # Commented: Smart Suggestion Feature
        return 0.0

    @extend_schema_field(serializers.ListField(child=serializers.JSONField()))
    def get_assignee_details(self, obj):
        # Commented: Smart Suggestion Feature
        # from tasks.calculations import calculate_final_assignment_score
        if obj.assignee:
            return [
                {
                    "id": str(obj.assignee.id), 
                    "name": obj.assignee.get_full_name() or obj.assignee.email, 
                    "email": obj.assignee.email,
                    "initial": (obj.assignee.email[0] if obj.assignee.email else 'U').upper(),
                    "employee_score": None,
                    "fatigue_score": None,
                    "match_score": None
                }
            ]
        return []

    @extend_schema_field(serializers.ListField(child=serializers.JSONField()))
    def get_watcher_details(self, obj):
        return [
            {"id": str(user.id), "name": user.get_full_name() or user.email, "email": user.email} 
            for user in obj.watchers.all()
        ]

    @extend_schema_field(serializers.ListField(child=serializers.JSONField()))
    def get_shared_viewer_details(self, obj):
        return [
            {"id": str(user.id), "name": user.get_full_name() or user.email, "email": user.email} 
            for user in obj.shared_viewers.all()
        ]

    @extend_schema_field(serializers.FloatField())
    def get_days_needed(self, obj):
        from tasks.utils import calculate_days_needed
        hours = obj.total_estimated_minutes / 60.0
        return round(calculate_days_needed(hours), 2)

    @extend_schema_field(serializers.DateTimeField(allow_null=True))
    def get_suggested_due_date(self, obj):
        from tasks.utils import suggest_realistic_due_date
        hours = obj.total_estimated_minutes / 60.0
        if hours <= 0.0:
            return None
        start = obj.start_date
        user_id = obj.assignee_id
        
        return suggest_realistic_due_date(
            start_date=start,
            estimated_hours=hours,
            user_id=user_id,
            organization_id=obj.organization_id,
            exclude_task_id=obj.id
        )

    @extend_schema_field(serializers.ListField(child=serializers.JSONField()))
    def get_load_warnings(self, obj):
        from tasks.utils import get_load_warnings
        if not obj.due_date:
            return []
        
        if obj.assignee:
            return get_load_warnings(
                user_id=obj.assignee.id,
                date=obj.due_date.date(),
                organization_id=obj.organization_id,
                exclude_task_id=obj.id
            )
        return []

    def validate(self, attrs):
        if 'assignees' in attrs:
            assignees_list = attrs.pop('assignees')
            attrs['assignee'] = assignees_list[0] if assignees_list else None
        return attrs

    @extend_schema_field(serializers.ListField(child=serializers.JSONField()))
    def get_tickets(self, obj):
        return [
            {
                "id": str(t.id),
                "assignee_name": t.assignee.get_full_name() or t.assignee.email,
                "assignee_email": t.assignee.email,
                "assignee": str(t.assignee_id),
                "status": t.status,
                "updated_at": t.updated_at.isoformat(),
                **get_ticket_timer_data(t),
            }
            for t in obj.tickets.all()
        ]

    @extend_schema_field(serializers.ListField(child=serializers.JSONField(), allow_null=True))
    def get_feedbacks(self, obj):
        request = self.context.get('request')
        if not request:
            return None
            
        from core.permissions import get_member_membership
        membership = get_member_membership(request, obj.organization_id)
        # Show feedback to admins/owners or the assignee themselves
        if membership and membership.role in ['admin', 'owner']:
            feedbacks = obj.feedbacks.all()
            return TaskFeedbackSerializer(feedbacks, many=True, context=self.context).data
        # If user is a member, they can only see their own feedback
        feedbacks = obj.feedbacks.filter(user=request.user)
        return TaskFeedbackSerializer(feedbacks, many=True, context=self.context).data

    @extend_schema_field(serializers.ListField(child=serializers.JSONField(), allow_null=True))
    def get_extension_requests(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        from core.permissions import get_member_membership
        membership = get_member_membership(request, obj.organization_id)
        if membership and membership.role in ['admin', 'owner']:
            extensions = obj.extension_requests.all()
        else:
            extensions = obj.extension_requests.filter(requested_by=request.user)
        return TaskExtensionRequestSerializer(extensions, many=True, context=self.context).data

    @extend_schema_field(serializers.JSONField(allow_null=True))
    def get_segments(self, obj):
        if obj.schedule_status == 'SCHEDULED' and obj.schedule_reason:
            import json
            try:
                # If the string starts with '[' it's a JSON list of segments
                if obj.schedule_reason.strip().startswith('['):
                    segs = json.loads(obj.schedule_reason)
                    from tasks.services.calendar import to_org_tz
                    from django.utils.dateparse import parse_datetime
                    for seg in segs:
                        if 'start' in seg:
                            dt_start = parse_datetime(seg['start'])
                            if dt_start:
                                seg['start'] = to_org_tz(dt_start, obj.organization).isoformat()
                        if 'end' in seg:
                            dt_end = parse_datetime(seg['end'])
                            if dt_end:
                                seg['end'] = to_org_tz(dt_end, obj.organization).isoformat()
                    return segs
            except Exception:
                pass
        return None

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        try:
            from tasks.services.calendar import to_org_tz
            if instance.planned_start:
                ret['planned_start'] = to_org_tz(instance.planned_start, instance.organization).isoformat()
            if instance.planned_end:
                ret['planned_end'] = to_org_tz(instance.planned_end, instance.organization).isoformat()
        except Exception:
            pass
        return ret

class TaskTicketSerializer(serializers.ModelSerializer):
    task_details = serializers.SerializerMethodField()
    assignee_details = serializers.SerializerMethodField()
    running_elapsed_seconds = serializers.SerializerMethodField()
    total_elapsed_seconds = serializers.SerializerMethodField()
    timer_started_at = serializers.SerializerMethodField()

    class Meta:
        model = TaskTicket
        fields = [
            'id', 'task', 'task_details', 'assignee', 'assignee_details', 'status',
            'time_spent_minutes', 'running_elapsed_seconds', 'total_elapsed_seconds',
            'timer_started_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'task', 'task_details', 'assignee', 'assignee_details', 'created_at', 'updated_at']

    def get_running_elapsed_seconds(self, obj):
        return get_ticket_timer_data(obj)["running_elapsed_seconds"]

    def get_total_elapsed_seconds(self, obj):
        return get_ticket_timer_data(obj)["total_elapsed_seconds"]

    def get_timer_started_at(self, obj):
        return get_ticket_timer_data(obj)["timer_started_at"]

    @extend_schema_field(serializers.JSONField())
    def get_task_details(self, obj):
        return {
            "id": str(obj.task.id),
            "title": obj.task.title,
            "description": obj.task.description,
            "priority": obj.task.priority,
            "due_date": obj.task.due_date.isoformat() if obj.task.due_date else None,
            "issue_type": obj.task.issue_type,
            "created_by": obj.task.created_by.get_full_name() if obj.task.created_by else None,
            "goal": str(obj.task.goal.id) if obj.task.goal else None,
            "goal_title": obj.task.goal.title if obj.task.goal else None,
        }

    @extend_schema_field(serializers.JSONField())
    def get_assignee_details(self, obj):
        return {
            "id": str(obj.assignee.id),
            "name": obj.assignee.get_full_name() or obj.assignee.email,
            "email": obj.assignee.email,
            "initial": (obj.assignee.email[0] if obj.assignee.email else 'U').upper()
        }

class TaskExtensionRequestSerializer(serializers.ModelSerializer):
    requested_by_details = serializers.SerializerMethodField()
    reviewed_by_details = serializers.SerializerMethodField()
    task_title = serializers.CharField(source='task.title', read_only=True)
    task_priority = serializers.CharField(source='task.priority', read_only=True)
    current_due_date = serializers.DateTimeField(source='task.due_date', read_only=True)

    class Meta:
        model = TaskExtensionRequest
        fields = [
            'id', 'task', 'task_title', 'task_priority', 'current_due_date', 
            'requested_by', 'requested_by_details', 'reason_type', 'reason_text',
            'proposed_date', 'requested_hours', 'status', 'manager_comment', 'reviewed_by', 'reviewed_by_details',
            'reviewed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'task', 'task_title', 'task_priority', 'current_due_date',
            'requested_by', 'status', 'manager_comment', 'reviewed_by', 'reviewed_at',
            'created_at', 'updated_at'
        ]

    @extend_schema_field(serializers.JSONField(allow_null=True))
    def get_requested_by_details(self, obj):
        user = obj.requested_by
        return {
            "id": str(user.id),
            "name": user.get_full_name() or user.email,
            "email": user.email,
            "initial": (user.first_name[0] if user.first_name else (user.email[0] if user.email else 'U')).upper()
        }

    @extend_schema_field(serializers.JSONField(allow_null=True))
    def get_reviewed_by_details(self, obj):
        user = obj.reviewed_by
        if not user:
            return None
        return {
            "id": str(user.id),
            "name": user.get_full_name() or user.email,
            "email": user.email,
            "initial": (user.first_name[0] if user.first_name else (user.email[0] if user.email else 'U')).upper()
        }

class TaskFeedbackSerializer(serializers.ModelSerializer):
    user_details = serializers.SerializerMethodField()
    
    class Meta:
        model = TaskFeedback
        fields = ['id', 'task', 'user', 'user_details', 'difficulty', 'comments', 'created_at']
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


class ManualScheduleSerializer(serializers.Serializer):
    user_id = serializers.UUIDField(required=True)
    organization_id = serializers.UUIDField(required=True)

    def validate(self, attrs):
        user_id = attrs.get('user_id')
        organization_id = attrs.get('organization_id')

        # Verify user exists
        if not User.objects.filter(id=user_id).exists():
            raise serializers.ValidationError({"user_id": "User does not exist."})

        # Verify organization exists
        from organizations.models import Organization
        if not Organization.objects.filter(id=organization_id).exists():
            raise serializers.ValidationError({"organization_id": "Organization does not exist."})

        # Verify user is a member of the organization
        from organizations.models import OrganizationMembership
        if not OrganizationMembership.objects.filter(
            user_id=user_id,
            organization_id=organization_id,
            is_active=True
        ).exists():
            raise serializers.ValidationError("User is not an active member of this organization.")

        return attrs
