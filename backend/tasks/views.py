from datetime import datetime
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from tasks.models import Task, TaskComment, TaskAttachment, TaskTicket, TaskExtensionRequest, TaskFeedback
from organizations.models import Organization, OrganizationMembership
from tasks.serializers import (
    TaskSerializer, TaskDetailSerializer,
    TaskCommentSerializer, TaskAttachmentSerializer,
    CommentListSerializer, CommentCreateSerializer, CommentUpdateSerializer,
    TaskTicketSerializer, TaskExtensionRequestSerializer,
    ManualScheduleSerializer
)
from core.permissions import get_member_membership, HasTaskPermissions, IsOrganizationAdmin
from core.pagination import StandardResultsSetPagination


def apply_automatic_task_schedule(task):
    if task.assignee:
        from tasks.services.scheduler import SchedulerService
        task = SchedulerService.schedule_single_task_in_earliest_gap(task)
    else:
        task.planned_start = None
        task.planned_end = None
        task.schedule_status = 'QUEUED'
        task.schedule_reason = "No assignee"
        task.save(update_fields=['planned_start', 'planned_end', 'schedule_status', 'schedule_reason', 'is_auto_scheduled'])

    return task


def build_task_create_response(task, request):
    from tasks.services.scheduler import get_task_schedule_details

    return {
        "message": "Task created successfully!",
        "scheduled_details": get_task_schedule_details(task),
        "task": TaskSerializer(task, context={'request': request}).data,
    }


def filter_visible_tasks(request, qs, organization):
    membership = get_member_membership(request, organization.id)
    if not membership or not membership.is_active:
        return qs.none()

    if membership.role in ['owner', 'admin']:
        return qs

    return qs.filter(
        Q(visibility_type='organization') |
        Q(created_by=request.user) |
        Q(assignee=request.user) |
        Q(watchers=request.user) |
        Q(visible_to=request.user) |
        Q(shared_viewers=request.user)
    ).distinct()


class CreateTaskView(APIView):
    permission_classes = [IsAuthenticated, HasTaskPermissions]

    @extend_schema(
        request=TaskSerializer,
        responses={201: TaskSerializer, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT},
        description="Create a new task under a specific organization and optionally link to a goal."
    )
    @transaction.atomic
    def post(self, request, goal_id=None):
        org_id = request.data.get('organization')
        organization = get_object_or_404(Organization, id=org_id)

        assignees = request.data.get('assignees', [])
        watchers = request.data.get('watchers', [])
        visible_to = request.data.get('visible_to', [])

        if isinstance(assignees, list):
            assignees = [u for u in assignees if u and str(u).strip() and str(u).lower() != 'null']
        else:
            assignees = []
            
        if isinstance(watchers, list):
            watchers = [w for w in watchers if w and str(w).strip() and str(w).lower() != 'null']
        else:
            watchers = []
            
        if isinstance(visible_to, list):
            visible_to = [v for v in visible_to if v and str(v).strip() and str(v).lower() != 'null']
        else:
            visible_to = []

        if hasattr(request.data, '_mutable'):
            old_mutable = request.data._mutable
            request.data._mutable = True
            request.data['assignees'] = assignees
            request.data['watchers'] = watchers
            request.data['visible_to'] = visible_to
            request.data._mutable = old_mutable
        else:
            try:
                request.data['assignees'] = assignees
                request.data['watchers'] = watchers
                request.data['visible_to'] = visible_to
            except TypeError:
                pass

        all_related_users = set([u for u in (assignees + watchers + visible_to) if str(u).strip()])
        if all_related_users:
            valid_member_count = OrganizationMembership.objects.filter(
                organization=organization,
                user_id__in=all_related_users,
                is_active=True
            ).count()
            if valid_member_count != len(all_related_users):
                return Response(
                    {"error": "One or more assignees, watchers, or visible users are not active members of this organization."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = TaskSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            assigned_at = timezone.now() if assignees else None
            
            from tasks.services.scheduler import get_schedule_preview
            total_hours = serializer.validated_data.get('estimated_hours')
            assignee_id = assignees[0] if assignees else None
            
            splits = []
            if total_hours and assignee_id:
                preview = get_schedule_preview(assignee_id=assignee_id, estimated_hours=total_hours, org_id=organization.id)
                if preview and preview.get("segments"):
                    from collections import defaultdict
                    from tasks.services.calendar import to_org_tz
                    daily_minutes = defaultdict(int)
                    for seg in preview["segments"]:
                        start_local = to_org_tz(seg["start"], organization)
                        daily_minutes[start_local.date()] += seg["duration"]
                    for day, mins in sorted(daily_minutes.items()):
                        splits.append(round(mins / 60.0, 2))
            
            is_parent = len(splits) > 1
            
            task = serializer.save(
                organization=organization,
                created_by=request.user,
                assigned_at=assigned_at,
                is_auto_scheduled=not is_parent,
                schedule_status='QUEUED' if is_parent else 'QUEUED'
            )
            
            if assignees:
                member = OrganizationMembership.objects.filter(organization=organization, user=request.user).first()
                if member and member.role == 'member':
                    forbidden_assignees = OrganizationMembership.objects.filter(
                        organization=organization,
                        user_id__in=assignees,
                        role__in=['admin', 'owner']
                    ).exists()
                    if forbidden_assignees:
                        task.delete()
                        return Response({"error": "Regular users cannot assign tasks to Admins or Owners."}, status=403)


            if watchers:
                task.watchers.set(watchers)

            if visible_to:
                task.visible_to.set(visible_to)

            if task.visibility_type == 'specific':
                task.visible_to.add(request.user)
                management_user_ids = OrganizationMembership.objects.filter(
                    organization=organization,
                    role__in=['owner', 'admin'],
                    is_active=True
                ).values_list('user_id', flat=True)
                if management_user_ids:
                    task.visible_to.add(*management_user_ids)

            if request.data.get('planned_start') or request.data.get('planned_end'):
                task.is_auto_scheduled = False

            if is_parent:
                for i, split_hrs in enumerate(splits):
                    part_title = f"{task.title} (Part {i+1})"
                    part_data = {
                        **request.data,
                        'title': part_title,
                        'estimated_hours': split_hrs,
                        'estimated_minutes': int(split_hrs * 60)
                    }
                    part_serializer = TaskSerializer(data=part_data, context={'request': request})
                    if part_serializer.is_valid():
                        part_task = part_serializer.save(
                            organization=organization,
                            created_by=request.user,
                            assigned_at=assigned_at,
                            parent=task,
                            is_auto_scheduled=not (request.data.get('planned_start') or request.data.get('planned_end'))
                        )
                        if watchers: part_task.watchers.set(watchers)
                        if visible_to: part_task.visible_to.set(visible_to)
                        if part_task.visibility_type == 'specific':
                            part_task.visible_to.add(request.user)
                            if management_user_ids: part_task.visible_to.add(*management_user_ids)
                        apply_automatic_task_schedule(part_task)
            else:
                task = apply_automatic_task_schedule(task)

            return Response(build_task_create_response(task, request), status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskListView(APIView):
    """
    Endpoint for listing organization tasks, respecting visibility rules.
    """
    permission_classes = [IsAuthenticated, HasTaskPermissions]

    @extend_schema(
        responses={200: TaskSerializer(many=True)},
        description="Retrieve all tasks in the organization that the user is permitted to see."
    )
    def get(self, request, org_id):
        organization = get_object_or_404(Organization, id=org_id)
        
        # Base queryset for non-deleted tasks
        tasks = Task.objects.filter(organization=organization, is_deleted=False)
        tasks = filter_visible_tasks(request, tasks, organization)
        
        # Pre-fetch for performance
        tasks = tasks.select_related('goal', 'created_by', 'assignee').prefetch_related('watchers', 'visible_to').order_by('-created_at')

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(tasks, request)
        if page is not None:
            serializer = TaskSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)

        return Response(TaskSerializer(tasks, many=True, context={'request': request}).data)


class TaskDetailView(APIView):
    """
    Endpoint to retrieve, update, or delete a single task.
    """
    permission_classes = [IsAuthenticated, HasTaskPermissions]

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH']:
            return [IsAuthenticated(), HasTaskPermissions(), HasTaskPermissions()]
        elif self.request.method == 'DELETE':
            return [IsAuthenticated(), HasTaskPermissions(), HasTaskPermissions()]
        return super().get_permissions()

    @extend_schema(
        responses={200: TaskDetailSerializer},
        description="Retrieve detailed view of a task including comments and attachments, respecting visibility."
    )
    def get(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)
        
        # Verify visibility
        visible_qs = filter_visible_tasks(request, Task.objects.filter(id=task_id), task.organization)
        if not visible_qs.exists():
            return Response({"error": "This task is private or you do not have permission to view it."}, status=403)

        return Response(TaskDetailSerializer(task, context={'request': request}).data)

    @extend_schema(
        request=TaskSerializer,
        responses={200: TaskSerializer, 400: OpenApiTypes.OBJECT},
        description="Update task fields."
    )
    def patch(self, request, task_id):
        return self.update(request, task_id, partial=True)

    @extend_schema(
        request=TaskSerializer,
        responses={200: TaskSerializer, 400: OpenApiTypes.OBJECT},
        description="Replace task fields."
    )
    def put(self, request, task_id):
        return self.update(request, task_id, partial=False)

    def update(self, request, task_id, partial=False):
        task = get_object_or_404(Task, id=task_id)
        
        # Ensure it's not private to them first
        visible_qs = filter_visible_tasks(request, Task.objects.filter(id=task_id), task.organization)
        if not visible_qs.exists():
            return Response({"error": "This task is private or you do not have permission to access it."}, status=403)

        # Check permission constraints on the specific object
        self.check_object_permissions(request, task)

        # Validate assignment if assignees are modified
        if 'assignees' in request.data:
            assignees = request.data.get('assignees', [])
            if assignees:
                valid_member_count = OrganizationMembership.objects.filter(
                    organization=task.organization,
                    user_id__in=assignees,
                    is_active=True
                ).count()
                if valid_member_count != len(assignees):
                    return Response({"error": "One or more assignees are not members of the organization."}, status=400)

        old_planned_start = task.planned_start
        old_planned_end = task.planned_end
        old_assignee_id = task.assignee_id

        serializer = TaskSerializer(task, data=request.data, partial=partial, context={'request': request})
        if serializer.is_valid():
            if any(f in request.data for f in ['estimated_hours', 'estimated_minutes', 'planned_start', 'planned_end']):
                task._skip_dynamic_reschedule = True
            updated_task = serializer.save()
            
            has_start = 'planned_start' in request.data
            has_end = 'planned_end' in request.data
            has_est = 'estimated_hours' in request.data or 'estimated_minutes' in request.data
            
            needs_resave = False
            
            if has_start and not has_end:
                from tasks.services.scheduler import SchedulerService
                recalculated = SchedulerService.recalculate_task_window(updated_task, start_time=updated_task.planned_start)
                if recalculated:
                    updated_task.planned_start = recalculated["planned_start"]
                    updated_task.planned_end = recalculated["planned_end"]
                    updated_task.schedule_reason = recalculated["schedule_reason"]
                    updated_task.schedule_status = 'SCHEDULED'
                    needs_resave = True
            elif has_est and not has_end:
                from tasks.services.scheduler import SchedulerService
                recalculated = SchedulerService.recalculate_task_window(updated_task, start_time=updated_task.planned_start)
                if recalculated:
                    updated_task.planned_start = recalculated["planned_start"]
                    updated_task.planned_end = recalculated["planned_end"]
                    updated_task.schedule_reason = recalculated["schedule_reason"]
                    updated_task.schedule_status = 'SCHEDULED'
                    needs_resave = True
            elif has_end and not has_start:
                from tasks.services.calendar import calculate_working_hours
                if updated_task.planned_start and updated_task.planned_end:
                    # Pass the assignee User object so per-user schedule is respected
                    hrs = calculate_working_hours(updated_task.planned_start, updated_task.planned_end, updated_task.organization, user=updated_task.assignee)
                    updated_task.estimated_hours = round(hrs, 2)
                    updated_task.estimated_minutes = int(round(hrs * 60))
                    needs_resave = True
            elif has_start and has_end:
                from tasks.services.calendar import calculate_working_hours
                if updated_task.planned_start and updated_task.planned_end:
                    hrs = calculate_working_hours(updated_task.planned_start, updated_task.planned_end, updated_task.organization, user=updated_task.assignee)
                    updated_task.estimated_hours = round(hrs, 2)
                    updated_task.estimated_minutes = int(round(hrs * 60))
                    needs_resave = True

            # Pin task if user manually overrides the schedule
            if has_start or has_end:
                updated_task.is_auto_scheduled = False
                needs_resave = True
                
            if needs_resave:
                updated_task._skip_dynamic_reschedule = True
                updated_task.save(update_fields=[
                    'planned_start', 'planned_end', 'estimated_hours',
                    'estimated_minutes', 'is_auto_scheduled',
                    'schedule_status', 'schedule_reason'
                ])
            
            # Dynamic Task Reflow: Check if any key scheduling field changed
            trigger_fields = [
                'estimated_hours', 'estimated_minutes', 
                'planned_start', 'planned_end', 'due_date', 
                'priority', 'assignee', 'assignees', 'status'
            ]
            
            has_trigger_change = any(f in request.data for f in trigger_fields)
            
            if has_trigger_change and updated_task.status not in ['done', 'cancelled', 'archived']:
                from tasks.services.scheduler import SchedulerService

                # Run the cascade before serializing the response so Task
                # Details receives the post-shift schedule immediately after
                # "Save Changes" is clicked.
                if old_assignee_id and old_assignee_id != updated_task.assignee_id:
                    SchedulerService.schedule_tasks_for_assignee(old_assignee_id, updated_task.organization_id)

                if updated_task.assignee_id:
                    SchedulerService.cascade_reschedule_tasks(
                        updated_task.assignee,
                        updated_task.id,
                        old_planned_start,
                        old_planned_end
                    )
                    updated_task.refresh_from_db()
            
            return Response({
                "message": "Task updated successfully!",
                "task": TaskDetailSerializer(updated_task, context={'request': request}).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={204: None},
        description="Hard delete a task (only Owners/Admins or Task Creator)."
    )
    def delete(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)
        self.check_object_permissions(request, task)
        org_id = task.organization_id
        assignee_id = task.assignee_id
        start_dt = task.planned_start
        task.delete()
        
        if assignee_id:
            from django.db import transaction
            def do_dynamic_reschedule():
                from tasks.services.scheduler import SchedulerService
                from django.utils import timezone
                now = timezone.now()
                reflow = start_dt if start_dt and start_dt > now else now
                SchedulerService.reschedule_from_datetime(assignee_id, org_id, reflow)
            transaction.on_commit(do_dynamic_reschedule)
            
        return Response(status=status.HTTP_204_NO_CONTENT)


class UpdateTaskStatusView(APIView):
    """
    Specialized endpoint to update a task's status or assignees with strict permissions.
    """
    permission_classes = [IsAuthenticated, HasTaskPermissions]

    @extend_schema(
        request=TaskSerializer,
        responses={200: TaskSerializer, 400: OpenApiTypes.OBJECT},
        description="Update task status or basic fields quickly."
    )
    def patch(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)
        self.check_object_permissions(request, task)
        
        if 'assignee' in request.data or 'assignees' in request.data:
            # Reassignment permission check
            is_creator = task.created_by == request.user
            is_goal_owner = task.goal and task.goal.owner == request.user
            membership = get_member_membership(request, task.organization.id)
            
            if not (is_creator or is_goal_owner or (membership and membership.role in ['owner', 'admin'])):
                return Response({"error": "You do not have permission to change assignees on this task."}, status=403)
            
            # Validate assignee list is member of the organization
            assignees = request.data.get('assignees', [])
            if not assignees and request.data.get('assignee'):
                assignees = [request.data.get('assignee')]
            
            if assignees:
                valid_count = OrganizationMembership.objects.filter(
                    organization=task.organization,
                    user_id__in=assignees,
                    is_active=True
                ).count()
                if valid_count != len(assignees):
                    return Response({"error": "One or more assignees are not members of the organization."}, status=400)
            request.data['assigned_at'] = timezone.now()

        old_assignee_id = task.assignee_id
        old_planned_start = task.planned_start
        
        serializer = TaskSerializer(task, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            updated_task = serializer.save()
            
            trigger_fields = ['status', 'assignee', 'assignees']
            has_trigger_change = any(f in request.data for f in trigger_fields)
            
            if has_trigger_change:
                from django.db import transaction
                def do_dynamic_reschedule_status():
                    from tasks.services.scheduler import SchedulerService
                    from django.utils import timezone
                    now = timezone.now()
                    reflow = old_planned_start if old_planned_start and old_planned_start > now else now
                    
                    if old_assignee_id and old_assignee_id != updated_task.assignee_id:
                        SchedulerService.reschedule_from_datetime(old_assignee_id, updated_task.organization_id, reflow)
                    
                    if updated_task.assignee_id:
                        SchedulerService.reschedule_from_datetime(updated_task.assignee_id, updated_task.organization_id, reflow)
                        
                transaction.on_commit(do_dynamic_reschedule_status)

            return Response({
                "message": "Task status updated successfully!",
                "task": TaskSerializer(updated_task, context={'request': request}).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SoftDeleteTaskView(APIView):
    """
    Endpoint to soft-delete tasks.
    """
    permission_classes = [IsAuthenticated, HasTaskPermissions]

    @extend_schema(
        responses={204: None},
        description="Soft delete a task (only Owners/Admins or Task Creator)."
    )
    def delete(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)
        self.check_object_permissions(request, task)
        org_id = task.organization_id
        assignee_id = task.assignee_id
        start_dt = task.planned_start
        task.delete()
        
        if assignee_id:
            from django.db import transaction
            def do_dynamic_reschedule_soft():
                from tasks.services.scheduler import SchedulerService
                from django.utils import timezone
                now = timezone.now()
                reflow = start_dt if start_dt and start_dt > now else now
                SchedulerService.reschedule_from_datetime(assignee_id, org_id, reflow)
            transaction.on_commit(do_dynamic_reschedule_soft)
            
        return Response(status=status.HTTP_204_NO_CONTENT)


class TrashView(APIView):
    """
    Retrieve soft-deleted tasks within the organization context.
    """
    permission_classes = [IsAuthenticated, HasTaskPermissions]

    @extend_schema(
        responses={200: TaskSerializer(many=True)},
        description="List all soft-deleted tasks in the organization."
    )
    def get(self, request, org_id):
        organization = get_object_or_404(Organization, id=org_id)
        tasks = Task.objects.filter(organization=organization, is_deleted=True)
        tasks = filter_visible_tasks(request, tasks, organization)
        tasks = tasks.select_related('goal', 'created_by', 'assignee').prefetch_related('watchers', 'visible_to').order_by('-updated_at')

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(tasks, request)
        if page is not None:
            serializer = TaskSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)

        return Response(TaskSerializer(tasks, many=True, context={'request': request}).data)


class RestoreTaskView(APIView):
    """
    Restore a soft-deleted task.
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, HasTaskPermissions]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        description="Restore a soft-deleted task."
    )
    def post(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)
        self.check_object_permissions(request, task)
        task.restore()
        return Response({"message": "Task restored successfully!"}, status=status.HTTP_200_OK)


class TaskCommentsListView(APIView):
    """
    Retrieve all top-level comments on a task (replies nested inside them).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: CommentListSerializer(many=True)},
        description="Retrieve all top-level comments on a task, with nested replies."
    )
    def get(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)
        visible_qs = filter_visible_tasks(request, Task.objects.filter(id=task_id), task.organization)
        if not visible_qs.exists():
            return Response({"error": "Access denied."}, status=403)

        # Retrieve only top-level comments; replies are serialized recursively
        comments = TaskComment.objects.filter(task_id=task_id, parent=None).order_by('created_at')
        return Response({"comments": CommentListSerializer(comments, many=True, context={'request': request}).data})


class CreateTaskCommentView(APIView):
    """
    Create a new comment or threaded reply on a task, with mention detection and attachment linking.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=CommentCreateSerializer,
        responses={201: CommentListSerializer},
        description="Post a comment or reply to a comment on a task. Detects @mentions."
    )
    def post(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)
        visible_qs = filter_visible_tasks(request, Task.objects.filter(id=task.id), task.organization)
        if not visible_qs.exists():
            return Response({"error": "Access denied."}, status=403)

        serializer = CommentCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            parent_comment = serializer.validated_data.get('parent')
            if parent_comment and parent_comment.task != task:
                return Response({"error": "Parent comment must belong to the same task."}, status=status.HTTP_400_BAD_REQUEST)

            comment_obj = serializer.save(task=task, user=request.user)

            # Mention detection
            from tasks.utils import extract_mentions
            mentioned_users = extract_mentions(comment_obj.comment)
            if mentioned_users:
                comment_obj.mentions.set(mentioned_users)

            # Attachment linking
            attachment_ids = request.data.get('attachment_ids', [])
            if attachment_ids:
                TaskAttachment.objects.filter(id__in=attachment_ids, task=task).update(comment=comment_obj)

            # Re-serialize to fetch nested fields
            return Response(CommentListSerializer(comment_obj, context={'request': request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReplyToCommentView(APIView):
    """
    Create a nested threaded reply to a specific comment.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=CommentCreateSerializer,
        responses={201: CommentListSerializer},
        description="Reply to a specific comment. Detects @mentions."
    )
    def post(self, request, comment_id):
        parent_comment = get_object_or_404(TaskComment, id=comment_id)
        task = parent_comment.task
        
        # Check task visibility
        visible_qs = filter_visible_tasks(request, Task.objects.filter(id=task.id), task.organization)
        if not visible_qs.exists():
            return Response({"error": "Access denied."}, status=403)

        serializer = CommentCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            comment_obj = serializer.save(task=task, user=request.user, parent=parent_comment)

            # Mention detection
            from tasks.utils import extract_mentions
            mentioned_users = extract_mentions(comment_obj.comment)
            if mentioned_users:
                comment_obj.mentions.set(mentioned_users)

            return Response(CommentListSerializer(comment_obj, context={'request': request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskCommentDetailView(APIView):
    """
    Retrieve, update (edit), or delete (soft delete) a specific comment.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=CommentUpdateSerializer,
        responses={200: CommentListSerializer},
        description="Edit the comment text. Sets is_edited=True and updates mentions."
    )
    def put(self, request, comment_id):
        comment_obj = get_object_or_404(TaskComment, id=comment_id)
        # Check task visibility permissions
        task = comment_obj.task
        visible_qs = filter_visible_tasks(request, Task.objects.filter(id=task.id), task.organization)
        if not visible_qs.exists():
            return Response({"error": "Access denied."}, status=403)

        # Only comment author can edit
        if comment_obj.user != request.user:
            return Response({"error": "You do not have permission to edit this comment."}, status=403)

        serializer = CommentUpdateSerializer(comment_obj, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            new_comment = serializer.validated_data.get('comment')
            if new_comment and new_comment != comment_obj.comment:
                comment_obj.is_edited = True
                
                # Re-run mention detection
                from tasks.utils import extract_mentions
                mentioned_users = extract_mentions(new_comment)
                comment_obj.mentions.set(mentioned_users)

            comment_obj = serializer.save()
            return Response(CommentListSerializer(comment_obj, context={'request': request}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        description="Soft delete a comment."
    )
    def delete(self, request, comment_id):
        comment_obj = get_object_or_404(TaskComment, id=comment_id)
        task = comment_obj.task
        
        # Check organization membership
        membership = get_member_membership(request, task.organization.id)
        if not membership or not membership.is_active:
            return Response({"error": "Access denied."}, status=403)

        # Only the comment author or an owner/admin of the organization can delete
        is_author = comment_obj.user == request.user
        is_admin_or_owner = membership.role in ['owner', 'admin']

        if not (is_author or is_admin_or_owner):
            return Response({"error": "You do not have permission to delete this comment."}, status=403)

        comment_obj.soft_delete()
        return Response({"message": "Comment deleted successfully."}, status=status.HTTP_200_OK)


class TaskAttachmentUploadView(APIView):
    """
    Upload an attachment to a task.
    """
    serializer_class = TaskAttachmentSerializer
    permission_classes = [IsAuthenticated, HasTaskPermissions]

    @extend_schema(
        responses={201: TaskAttachmentSerializer},
        description="Upload a file attachment to a task."
    )
    def post(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)
        self.check_object_permissions(request, task)

        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        attachment = TaskAttachment.objects.create(
            task=task, 
            file=file_obj, 
            file_name=file_obj.name, 
            uploaded_by=request.user
        )
        return Response(TaskAttachmentSerializer(attachment).data, status=status.HTTP_201_CREATED)


class BulkTaskUpdateView(APIView):
    """
    Bulk update tasks in an organization.
    """
    permission_classes = [IsAuthenticated, HasTaskPermissions]

    @extend_schema(
        request=OpenApiTypes.OBJECT,
        responses={200: OpenApiTypes.OBJECT},
        description="Bulk update multiple tasks in the organization."
    )
    def post(self, request, org_id):
        organization = get_object_or_404(Organization, id=org_id)
        membership = get_member_membership(request, organization.id)
        
        # Restrict bulk operations to owners and admins
        if not membership or membership.role not in ['owner', 'admin']:
            return Response({"error": "Only Admins or Owners can perform bulk updates."}, status=status.HTTP_403_FORBIDDEN)

        task_ids = request.data.get('task_ids', [])
        updates = request.data.get('updates', {})
        
        # Prevent mutating organization in bulk tasks
        if 'organization' in updates:
            updates.pop('organization')

        updated_count = Task.objects.filter(id__in=task_ids, organization=organization).update(**updates)
        return Response({"message": f"Successfully updated {updated_count} tasks."}, status=status.HTTP_200_OK)


class QuickAssignTaskView(APIView):
    """
    Quickly assign a user to a task.
    """
    permission_classes = [IsAuthenticated, HasTaskPermissions]
    @extend_schema(
        request=OpenApiTypes.OBJECT,
        responses={200: OpenApiTypes.OBJECT},
        description="Quickly append an assignee to a task."
    )
    def post(self, request):
        task_id = request.data.get('task_id')
        user_id = request.data.get('user_id')
        task = get_object_or_404(Task, id=task_id)

        # Verify visibility and edit permissions
        visible_qs = filter_visible_tasks(request, Task.objects.filter(id=task_id), task.organization)
        if not visible_qs.exists():
            return Response({"error": "Access denied."}, status=403)

        self.check_object_permissions(request, task)

        from users.models import User
        user = get_object_or_404(User, id=user_id)

        # Verify target user is in the same organization
        is_member = OrganizationMembership.objects.filter(organization=task.organization, user=user, is_active=True).exists()
        if not is_member:
            return Response({"error": "Target user is not a member of this organization."}, status=400)

        task.assignee = user
        task.save(update_fields=['assignee'])
        return Response({"message": f"User {user.email} assigned to task successfully."}, status=status.HTTP_200_OK)


class FilteredTasksView(APIView):
    """
    Endpoint to retrieve list of tasks with custom filters (my_tasks, assigned_to_me, goals, etc.).
    """
    permission_classes = [IsAuthenticated, HasTaskPermissions]

    @extend_schema(
        parameters=[
            OpenApiParameter('status', OpenApiTypes.STR, description="Filter by task status"),
            OpenApiParameter('priority', OpenApiTypes.STR, description="Filter by task priority"),
            OpenApiParameter('assignee', OpenApiTypes.STR, description="Filter by assignee user ID"),
            OpenApiParameter('goal', OpenApiTypes.STR, description="Filter by linked Goal ID"),
            OpenApiParameter('my_tasks', OpenApiTypes.BOOL, description="Filter only tasks created by or assigned to request user"),
        ],
        responses={200: OpenApiTypes.OBJECT},
        description="Retrieve filtered lists of tasks under the organization context."
    )
    def get(self, request, org_id):
        organization = get_object_or_404(Organization, id=org_id)
        
        queryset = Task.objects.filter(organization=organization, is_deleted=False)
        queryset = filter_visible_tasks(request, queryset, organization)

        status_param = request.query_params.get('status')
        priority = request.query_params.get('priority')
        assignee = request.query_params.get('assignee')
        goal = request.query_params.get('goal')
        my_tasks = request.query_params.get('my_tasks')

        if status_param:
            queryset = queryset.filter(status=status_param)
        if priority:
            queryset = queryset.filter(priority=priority)
        if assignee:
            queryset = queryset.filter(assignee_id=assignee)
        if goal:
            queryset = queryset.filter(goal_id=goal)
        if my_tasks and my_tasks.lower() == 'true':
            queryset = queryset.filter(Q(created_by=request.user) | Q(assignee=request.user)).distinct()

        queryset = queryset.select_related('goal', 'created_by', 'assignee').prefetch_related('watchers').order_by('-created_at')
        serializer = TaskSerializer(queryset, many=True, context={'request': request})
        return Response({
            "total": queryset.count(),
            "tasks": serializer.data
        }, status=status.HTTP_200_OK)


class RemoveTaskAssigneeView(APIView):
    """
    Endpoint to remove a specific assignee from a task.
    """
    permission_classes = [IsAuthenticated, HasTaskPermissions]

    @extend_schema(
        request=OpenApiTypes.OBJECT,
        responses={200: OpenApiTypes.OBJECT},
        description="Remove a specific assignee from a task."
    )
    def patch(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)
        self.check_object_permissions(request, task)
        
        assignee_id = request.data.get('assignee_id')
        if not assignee_id:
            return Response({"error": "assignee_id is required."}, status=400)
            
        if task.assignee_id and str(task.assignee_id) == str(assignee_id):
            task.assignee = None
            task.save(update_fields=['assignee'])

        return Response({"message": "Assignee removed successfully."}, status=status.HTTP_200_OK)


class TaskPlanningHelperView(APIView):
    """
    Intelligent helper to suggest realistic due dates, calculate days needed,
    and detect overload warnings before a task is created or updated.
    """
    permission_classes = [IsAuthenticated, HasTaskPermissions]

    @extend_schema(
        parameters=[
            OpenApiParameter('organization', OpenApiTypes.UUID, required=True, description="Organization ID"),
            OpenApiParameter('estimated_hours', OpenApiTypes.FLOAT, required=False, description="Estimated hours"),
            OpenApiParameter('estimated_minutes', OpenApiTypes.INT, required=False, description="Estimated minutes"),
            OpenApiParameter('start_date', OpenApiTypes.DATE, required=False, description="Start date (YYYY-MM-DD)"),
            OpenApiParameter('due_date', OpenApiTypes.DATE, required=False, description="Proposed Due date (YYYY-MM-DD)"),
            OpenApiParameter('assignees', OpenApiTypes.STR, required=False, description="Comma-separated assignee user IDs"),
            OpenApiParameter('exclude_task_id', OpenApiTypes.UUID, required=False, description="Exclude task ID from load calculation"),
        ],
        responses={200: OpenApiTypes.OBJECT},
        description="Helper for break-aware planning and daily load warning calculations."
    )
    def get(self, request):
        import uuid
        org_id = request.query_params.get('organization')
        if not org_id:
            return Response({"error": "organization parameter is required."}, status=400)
            
        organization = get_object_or_404(Organization, id=org_id)
        
        # Estimate conversion
        est_hours = request.query_params.get('estimated_hours')
        est_mins = request.query_params.get('estimated_minutes')
        
        hours = 0.0
        if est_hours:
            hours = float(est_hours)
        elif est_mins:
            hours = int(est_mins) / 60.0
            
        start_date_str = request.query_params.get('start_date')
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response({"error": "Invalid start_date format. Use YYYY-MM-DD."}, status=400)
        else:
            start_date = timezone.now().date()
            
        due_date_str = request.query_params.get('due_date')
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response({"error": "Invalid due_date format. Use YYYY-MM-DD."}, status=400)

        assignee_ids_str = request.query_params.get('assignees')
        assignee_ids = []
        if assignee_ids_str:
            assignee_ids = [uuid.UUID(uid.strip()) for uid in assignee_ids_str.split(',') if uid.strip()]
            
        exclude_task_id = request.query_params.get('exclude_task_id')

        # Calculations
        from tasks.utils import calculate_days_needed, suggest_realistic_due_date, get_load_warnings
        days_needed = calculate_days_needed(hours)
        
        # For suggestion, we use the first assignee if available
        first_assignee_id = assignee_ids[0] if assignee_ids else None
        suggested_dt = suggest_realistic_due_date(
            start_date=start_date,
            estimated_hours=hours,
            user_id=first_assignee_id,
            organization_id=organization.id,
            exclude_task_id=exclude_task_id
        )
        
        # Load warnings
        warnings = []
        if due_date and assignee_ids:
            for uid in assignee_ids:
                warnings.extend(
                    get_load_warnings(
                        user_id=uid,
                        date=due_date,
                        organization_id=organization.id,
                        exclude_task_id=exclude_task_id
                    )
                )
                
        return Response({
            "estimated_hours": hours,
            "days_needed": round(days_needed, 2),
            "suggested_due_date": suggested_dt.isoformat() if suggested_dt else None,
            "warnings": warnings
        })


from rest_framework import generics
from rest_framework.exceptions import PermissionDenied, ValidationError

class OrgSlugMixin:
    def get_organization(self):
        org_slug = self.kwargs.get('org_slug')
        return get_object_or_404(Organization, slug=org_slug)

class OrgTaskListView(OrgSlugMixin, generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, HasTaskPermissions]
    
    def get_serializer_class(self):
        return TaskSerializer

    def get_queryset(self):
        org = self.get_organization()
        user = self.request.user
        queryset = Task.objects.filter(organization=org, is_deleted=False)

        membership = get_member_membership(self.request, org.id)
        if not membership or not membership.is_active:
            raise PermissionDenied("You are not an active member of this organization.")

        if membership.role in ['owner', 'admin']:
            return queryset.order_by('-created_at')

        from django.db.models import Q
        return queryset.filter(
            Q(sharing_option='organization') |
            Q(sharing_option='specific', assignee=user) |
            Q(sharing_option='specific', shared_viewers=user) |
            Q(sharing_option='private', assignee=user) |
            Q(created_by=user)
        ).distinct().order_by('-created_at')

    def create(self, request, *args, **kwargs):
        import json, traceback
        log_entry = {
            "endpoint": "OrgTaskListView.create",
            "data": request.data,
            "error": None,
            "traceback": None
        }
        try:
            response = super().create(request, *args, **kwargs)
            task = getattr(self, 'created_task', None)
            if task:
                res_data = build_task_create_response(task, request)
                return Response(res_data, status=response.status_code)
            return response
        except Exception as e:
            log_entry["error"] = str(getattr(e, 'detail', str(e)))
            log_entry["traceback"] = traceback.format_exc()
            raise e
        finally:
            try:
                with open("c:\\Users\\saura\\ParseOps\\backend\\debug_requests.txt", "a") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception:
                pass

    def post(self, request, *args, **kwargs):
        assignees = request.data.get('assignees', [])
        watchers = request.data.get('watchers', [])
        visible_to = request.data.get('visible_to', [])
        shared_viewers = request.data.get('shared_viewers', [])

        # Clean/normalize arrays (remove empty, null, or undefined placeholders from frontend)
        if isinstance(assignees, list):
            assignees = [u for u in assignees if u and str(u).strip() and str(u).lower() != 'null']
        else:
            assignees = []
            
        if isinstance(watchers, list):
            watchers = [w for w in watchers if w and str(w).strip() and str(w).lower() != 'null']
        else:
            watchers = []
            
        if isinstance(visible_to, list):
            visible_to = [v for v in visible_to if v and str(v).strip() and str(v).lower() != 'null']
        else:
            visible_to = []

        if isinstance(shared_viewers, list):
            shared_viewers = [s for s in shared_viewers if s and str(s).strip() and str(s).lower() != 'null']
        else:
            shared_viewers = []

        # Update request.data to contain the cleaned lists so the serializer doesn't get dirty values
        if hasattr(request.data, '_mutable'):
            old_mutable = request.data._mutable
            request.data._mutable = True
            request.data['assignees'] = assignees
            request.data['watchers'] = watchers
            request.data['visible_to'] = visible_to
            request.data['shared_viewers'] = shared_viewers
            request.data._mutable = old_mutable
        else:
            try:
                request.data['assignees'] = assignees
                request.data['watchers'] = watchers
                request.data['visible_to'] = visible_to
                request.data['shared_viewers'] = shared_viewers
            except TypeError:
                pass

        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        org = self.get_organization()
        assignees = self.request.data.get('assignees', [])
        
        watchers = self.request.data.get('watchers', [])
        visible_to = self.request.data.get('visible_to', [])
        shared_viewers = self.request.data.get('shared_viewers', [])
        all_related_users = set(assignees + watchers + visible_to + shared_viewers)
        if all_related_users:
            valid_member_count = OrganizationMembership.objects.filter(
                organization=org,
                user_id__in=all_related_users,
                is_active=True
            ).count()
            if valid_member_count != len(all_related_users):
                raise ValidationError({"error": "One or more assignees, watchers, shared viewers, or visible users are not active members of this organization."})

        assigned_at = timezone.now() if assignees else None
        task = serializer.save(
            organization=org,
            created_by=self.request.user,
            assigned_at=assigned_at
        )

        if assignees:
            member = OrganizationMembership.objects.filter(organization=org, user=self.request.user).first()
            if member and member.role == 'member':
                forbidden_assignees = OrganizationMembership.objects.filter(
                    organization=org,
                    user_id__in=assignees,
                    role__in=['admin', 'owner']
                ).exists()
                if forbidden_assignees:
                    task.delete()
                    raise PermissionDenied("Regular users cannot assign tasks to Admins or Owners.")

        self.created_task = apply_automatic_task_schedule(task)


class OrgTaskDetailView(OrgSlugMixin, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, HasTaskPermissions]
    queryset = Task.objects.filter(is_deleted=False)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return TaskSerializer
        return TaskDetailSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Track old values to determine delta
        old_planned_start = instance.planned_start
        old_planned_end = instance.planned_end
        old_assignee_id = instance.assignee_id

        serializer = TaskSerializer(instance, data=request.data, partial=partial, context={'request': request})
        serializer.is_valid(raise_exception=True)
        if any(f in request.data for f in ['estimated_hours', 'estimated_minutes', 'planned_start', 'planned_end']):
            instance._skip_dynamic_reschedule = True
        task = serializer.save()

        # Determine which scheduling fields the frontend sent
        has_est = 'estimated_hours' in request.data or 'estimated_minutes' in request.data
        has_start = 'planned_start' in request.data
        has_end = 'planned_end' in request.data
        
        needs_resave = False
        
        # ── Backend-driven Recalculation ──
        # The frontend provides local preview values, but the backend recalculates
        # authoritatively using SchedulerService / calendar utilities.
        
        if has_start and not has_end:
            # Start changed -> recalculate end from exact working duration.
            from tasks.services.scheduler import SchedulerService
            recalculated = SchedulerService.recalculate_task_window(task, start_time=task.planned_start)
            if recalculated:
                task.planned_start = recalculated["planned_start"]
                task.planned_end = recalculated["planned_end"]
                task.schedule_reason = recalculated["schedule_reason"]
                task.schedule_status = 'SCHEDULED'
                needs_resave = True

        elif has_est and not has_end:
            # Estimated duration changed -> keep start and recalculate end.
            from tasks.services.scheduler import SchedulerService
            from django.utils import timezone as tz
            start = task.planned_start or tz.now()
            recalculated = SchedulerService.recalculate_task_window(task, start_time=start)
            if recalculated:
                task.planned_start = recalculated["planned_start"]
                task.planned_end = recalculated["planned_end"]
                task.schedule_reason = recalculated["schedule_reason"]
                task.schedule_status = 'SCHEDULED'
                needs_resave = True

        elif has_end and not has_start:
            # End changed -> recalculate estimated hours from working minutes.
            from tasks.services.calendar import calculate_working_hours
            if task.planned_start and task.planned_end:
                hrs = calculate_working_hours(
                    task.planned_start, task.planned_end, task.organization,
                    user=task.assignee
                )
                task.estimated_hours = round(hrs, 2)
                task.estimated_minutes = int(round(hrs * 60))
                needs_resave = True

        elif has_start and has_end:
            # Both changed -> recalculate estimated hours to match the new window.
            from tasks.services.calendar import calculate_working_hours
            if task.planned_start and task.planned_end:
                hrs = calculate_working_hours(
                    task.planned_start, task.planned_end, task.organization,
                    user=task.assignee
                )
                task.estimated_hours = round(hrs, 2)
                task.estimated_minutes = int(round(hrs * 60))
                needs_resave = True

        # Pin task as manually scheduled if user set start/end directly
        if has_start or has_end:
            task.is_auto_scheduled = False
            needs_resave = True

        if needs_resave:
            task._skip_dynamic_reschedule = True
            task.save(update_fields=[
                'planned_start', 'planned_end', 'estimated_hours',
                'estimated_minutes', 'is_auto_scheduled',
                'schedule_status', 'schedule_reason'
            ])

        # ── Cascade Rescheduling ──
        # When any scheduling field changes, cascade-shift subsequent auto-scheduled tasks
        trigger_fields = [
            'estimated_hours', 'estimated_minutes',
            'planned_start', 'planned_end', 'due_date',
            'priority', 'assignee', 'assignees', 'status'
        ]
        has_trigger_change = any(f in request.data for f in trigger_fields)

        if has_trigger_change and task.status not in ['done', 'cancelled', 'archived']:
            from tasks.services.scheduler import SchedulerService

            # If assignee changed, reschedule old assignee's timeline too.
            if old_assignee_id and old_assignee_id != task.assignee_id:
                SchedulerService.schedule_tasks_for_assignee(old_assignee_id, task.organization_id)

            # Cascade before refresh/serialization so Save Changes reflects
            # shifted subsequent tasks immediately.
            if task.assignee_id:
                SchedulerService.cascade_reschedule_tasks(
                    task.assignee,
                    task.id,
                    old_planned_start,
                    old_planned_end
                )

        # Refresh and return
        task.refresh_from_db()

        if getattr(task, '_prefetched_objects_cache', None):
            task._prefetched_objects_cache = {}

        detail_serializer = TaskDetailSerializer(task, context={'request': request})
        return Response(detail_serializer.data)

    def perform_update(self, serializer):
        task = serializer.save()

    def perform_destroy(self, instance):
        instance.delete()


class TaskKanbanView(APIView):
    """
    Kanban Board View for individual TaskTickets:
    - Member: Can only see their assigned tickets (where assignee = request.user).
    - Owner/Admin: Can see all tickets in the organization.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: TaskTicketSerializer(many=True)},
        description="Retrieve all task tickets for the Kanban board inside a specific organization slug or ID."
    )
    def get(self, request, org_id):
        organization = get_object_or_404(Organization, id=org_id)
        membership = get_member_membership(request, organization.id)
        if not membership or not membership.is_active:
            return Response({"detail": "Not a member of this organization."}, status=status.HTTP_403_FORBIDDEN)

        # Self-healing: make sure any assignee on past/existing tasks has individual TaskTicket records
        active_tasks = Task.objects.filter(organization=organization, is_deleted=False, assignee__isnull=False)
        for t in active_tasks:
            if not TaskTicket.objects.filter(task=t, assignee=t.assignee).exists():
                TaskTicket.objects.create(
                    task=t,
                    assignee=t.assignee,
                    status=t.status
                )

        # Start with all tickets in the organization
        qs = TaskTicket.objects.filter(task__organization=organization, task__is_deleted=False)

        # Visibility Filter:
        # Standard Member: Can only see their own tickets
        # Owner/Admin: Can see all tickets in the organization
        if membership.role not in ['owner', 'admin']:
            qs = qs.filter(assignee=request.user)

        serializer = TaskTicketSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpdateTaskTicketStatusView(APIView):
    """
    Endpoint for updating the status of a specific TaskTicket:
    - Member: Can only update the status of THEIR OWN tickets.
    - Owner/Admin: Can update the status of ANY ticket in the organization.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=OpenApiTypes.OBJECT,
        responses={200: TaskTicketSerializer, 403: OpenApiTypes.OBJECT},
        description="Update status of an individual ticket."
    )
    def patch(self, request, ticket_id):
        ticket = get_object_or_404(TaskTicket, id=ticket_id)
        organization = ticket.task.organization
        membership = get_member_membership(request, organization.id)
        if not membership or not membership.is_active:
            return Response({"detail": "Not a member of this organization."}, status=status.HTTP_403_FORBIDDEN)

        # Permissions check:
        # Standard Member: Can only update their own ticket
        if membership.role not in ['owner', 'admin'] and ticket.assignee != request.user:
            return Response({"detail": "You do not have permission to update this ticket."}, status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get('status')
        add_time = request.data.get('add_time_minutes')
        
        if not new_status and add_time is None:
            return Response({"detail": "Provide status or add_time_minutes."}, status=status.HTTP_400_BAD_REQUEST)

        if new_status:
            valid_statuses = [c[0] for c in Task.STATUS_CHOICES]
            if new_status not in valid_statuses:
                return Response({"status": f"Invalid status. Must be one of {valid_statuses}."}, status=status.HTTP_400_BAD_REQUEST)
                            # Busy check removed to allow multiple tasks to be assigned/in-progress
            pass

            ticket.status = new_status
            
        if add_time:
            try:
                ticket.time_spent_minutes += int(add_time)
            except ValueError:
                return Response({"detail": "add_time_minutes must be an integer."}, status=status.HTTP_400_BAD_REQUEST)

        # Check for overrun
        parent_task = ticket.task
        est_mins = parent_task.estimated_minutes
        if not est_mins and parent_task.estimated_hours:
            est_mins = int(float(parent_task.estimated_hours) * 60)
            
        if est_mins:
            total_spent = sum(t.time_spent_minutes for t in parent_task.tickets.exclude(id=ticket.id)) + ticket.time_spent_minutes
            if total_spent >= est_mins:
                # Force status to paused to prevent further work
                ticket.status = 'paused'
                new_status = 'paused'
                
                if parent_task.status != 'delayed':
                    parent_task.status = 'delayed'
                    parent_task.save(update_fields=['status'])
                    
                    # Notify assignee and manager
                    from notifications.services import NotificationService
                    from organizations.models import OrganizationMembership
                    NotificationService.create_notification(
                        user=ticket.assignee,
                        title="Task Paused",
                        message=f"Your task '{parent_task.title}' exceeded its estimated time and was auto-paused. Please request an extension."
                    )
                    manager = OrganizationMembership.objects.filter(organization=organization, role__in=['owner', 'admin']).first()
                    if manager:
                        NotificationService.create_notification(
                            user=manager.user,
                            title="Task Overrun",
                            message=f"Task '{parent_task.title}' assigned to {ticket.assignee.email} has exceeded its estimated time and is delayed."
                        )

        ticket.save()
        
        # Auto-update parent task status if applicable
        if new_status:
            parent_task = ticket.task
            if new_status == 'in_progress' and parent_task.status == 'todo':
                parent_task.status = 'in_progress'
                parent_task.save(update_fields=['status'])
            elif new_status == 'in_review' and parent_task.status in ['todo', 'in_progress']:
                # Check if all tickets are in review or done
                all_tickets = parent_task.tickets.all()
                if all(t.status in ['in_review', 'done'] for t in all_tickets):
                    parent_task.status = 'in_review'
                    parent_task.save(update_fields=['status'])

        serializer = TaskTicketSerializer(ticket, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class TaskExtensionRequestView(APIView):
    """
    Endpoint for a task assignee to request an extension.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=TaskExtensionRequestSerializer,
        responses={201: TaskExtensionRequestSerializer},
        description="Create an extension request for a task"
    )
    def post(self, request, task_id):
        task = get_object_or_404(Task, id=task_id, is_deleted=False)
        organization = task.organization
        membership = get_member_membership(request, organization.id)
        if not membership or not membership.is_active:
            return Response({"detail": "Not a member of this organization."}, status=status.HTTP_403_FORBIDDEN)

        # Check if user is assignee
        if task.assignee_id != request.user.id:
            return Response({"detail": "Only task assignees can request an extension."}, status=status.HTTP_403_FORBIDDEN)

        if task.is_blocked:
            return Response({"detail": "This task is blocked from further extensions."}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure no pending request exists for this user/task
        from tasks.models import TaskExtensionRequest
        if TaskExtensionRequest.objects.filter(task=task, requested_by=request.user, status='pending').exists():
            return Response({"detail": "You already have a pending extension request for this task."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = TaskExtensionRequestSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(task=task, requested_by=request.user)
            
            try:
                from notifications.services import NotificationService
                manager = task.created_by
                if manager and manager != request.user:
                    NotificationService.send_notification(
                        recipient=manager,
                        n_type='extension_requested',
                        title='Extension Requested',
                        message=f"{request.user.first_name or request.user.email} requested an extension for task '{task.title}'.",
                        link=f"/tasks/{task.id}",
                        organization=organization
                    )
            except Exception as e:
                print("Failed to send extension request notification:", e)
                
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskExtensionListView(generics.ListAPIView):
    """
    Endpoint for Admin/Owner to view all extension requests in an organization.
    """
    serializer_class = TaskExtensionRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        org_id = self.kwargs.get('org_id')
        membership = get_member_membership(self.request, org_id)
        from tasks.models import TaskExtensionRequest
        if not membership or membership.role not in ['admin', 'owner']:
            return TaskExtensionRequest.objects.none()
        return TaskExtensionRequest.objects.filter(task__organization_id=org_id).order_by('-created_at')


class TaskExtensionReviewView(APIView):
    """
    Endpoint for Admin/Owner to approve, reject, or modify an extension request.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=OpenApiTypes.OBJECT,
        responses={200: TaskExtensionRequestSerializer},
        description="Review an extension request. Pass status (approved/rejected/modified), manager_comment, and optionally proposed_date (if modified)."
    )
    def patch(self, request, pk):
        from tasks.models import TaskExtensionRequest
        from django.utils import timezone
        
        ext_request = get_object_or_404(TaskExtensionRequest, id=pk)
        organization = ext_request.task.organization
        membership = get_member_membership(request, organization.id)
        
        if not membership or membership.role not in ['admin', 'owner']:
            return Response({"detail": "Only admins or owners can review extensions."}, status=status.HTTP_403_FORBIDDEN)

        if ext_request.status != 'pending':
            return Response({"detail": "This request has already been reviewed."}, status=status.HTTP_400_BAD_REQUEST)

        new_status = request.data.get('status')
        if new_status not in ['approved', 'rejected', 'modified']:
            return Response({"detail": "Invalid status. Must be approved, rejected, or modified."}, status=status.HTTP_400_BAD_REQUEST)

        ext_request.status = new_status
        ext_request.manager_comment = request.data.get('manager_comment', '')
        ext_request.reviewed_by = request.user
        ext_request.reviewed_at = timezone.now()

        if new_status == 'modified':
            new_date = request.data.get('proposed_date')
            if new_date:
                ext_request.proposed_date = new_date

        ext_request.save()

        # If approved or modified, update the task's due date and extension count
        if new_status in ['approved', 'modified']:
            task = ext_request.task
            task.due_date = ext_request.proposed_date
            task.extension_count += 1
            
            update_fields = ['due_date', 'extension_count', 'is_blocked']
            
            # Remove delayed status since extension is granted
            if task.status == 'delayed':
                total_spent = sum(t.time_spent_minutes for t in task.tickets.all())
                task.status = 'in_progress' if total_spent > 0 else 'todo'
                update_fields.append('status')
            
            if ext_request.requested_hours:
                from decimal import Decimal
                task.estimated_hours = (task.estimated_hours or Decimal('0.00')) + ext_request.requested_hours
                update_fields.extend(['estimated_hours'])

            # Auto-block if too many extensions (e.g., > 3)
            if task.extension_count >= 3:
                task.is_blocked = True
            task.save(update_fields=update_fields)
            
            # Auto-reschedule subsequent tasks dynamically on commit
            from django.db import transaction
            def do_dynamic_reschedule():
                from tasks.services.scheduler import SchedulerService
                from django.utils import timezone
                
                reflow_start = task.planned_start or timezone.now()
                SchedulerService.reschedule_from_datetime(task.assignee_id, task.organization_id, reflow_start)
                
            transaction.on_commit(do_dynamic_reschedule)

        # Send push notification to the requester
        try:
            from notifications.services import NotificationService
            title = f"Extension {new_status.capitalize()}"
            msg_body = f"Your extension request for '{ext_request.task.title}' was {new_status}."
            
            n_type = 'extension_approved' if new_status in ['approved', 'modified'] else 'extension_rejected'
            
            if new_status == 'modified':
                msg_body = f"Your extension for '{ext_request.task.title}' was approved with a modified date."
            
            NotificationService.send_notification(
                recipient=ext_request.requested_by,
                n_type=n_type,
                title=title,
                message=msg_body,
                link=f"/tasks/{ext_request.task.id}",
                organization=organization
            )
        except Exception as e:
            print("Failed to send extension review notification:", e)

        serializer = TaskExtensionRequestSerializer(ext_request, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CreateTaskFeedbackView(APIView):
    """
    Endpoint for a user to submit feedback after completing a task.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=OpenApiTypes.OBJECT,
        responses={201: OpenApiTypes.OBJECT},
        description="Submit post-task feedback (difficulty, comments)"
    )
    def post(self, request, task_id):
        from tasks.models import TaskFeedback
        from tasks.serializers import TaskFeedbackSerializer
        
        task = get_object_or_404(Task, id=task_id, is_deleted=False)
        organization = task.organization
        membership = get_member_membership(request, organization.id)
        if not membership or not membership.is_active:
            return Response({"detail": "Not a member of this organization."}, status=status.HTTP_403_FORBIDDEN)

        # Only assignees can leave feedback
        if task.assignee_id != request.user.id:
            return Response({"detail": "Only task assignees can submit feedback."}, status=status.HTTP_403_FORBIDDEN)

        # Only allow feedback if task is done
        if task.status != 'done':
            return Response({"detail": "Feedback can only be submitted for completed tasks."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if already submitted
        if TaskFeedback.objects.filter(task=task, user=request.user).exists():
            return Response({"detail": "You have already submitted feedback for this task."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = TaskFeedbackSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(task=task, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from .models import TaskSubmission
from .serializers import TaskSubmissionSerializer

class TaskSubmissionView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request=TaskSubmissionSerializer,
        responses={201: TaskSubmissionSerializer},
        description="Create a new task submission (proof) when a task is marked as done."
    )
    def post(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)
        organization = task.organization
        membership = get_member_membership(request, organization.id)
        if not membership or not membership.is_active:
            return Response({"detail": "Not a member of this organization."}, status=status.HTTP_403_FORBIDDEN)
            
        serializer = TaskSubmissionSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            submission = serializer.save(task=task, user=request.user)
            
            # Handle visible_to logic for 'specific' visibility
            visible_to_ids = request.data.get('visible_to', [])
            if isinstance(visible_to_ids, str):
                import json
                try:
                    visible_to_ids = json.loads(visible_to_ids)
                except:
                    visible_to_ids = []
            
            if visible_to_ids and submission.visibility == 'specific':
                submission.visible_to.set(visible_to_ids)
                
            return Response(TaskSubmissionSerializer(submission, context={'request': request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangeAssigneeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=OpenApiTypes.OBJECT,
        responses={200: OpenApiTypes.OBJECT},
        description="Owner override to set any assignee for a task, bypassing the busy check."
    )
    def patch(self, request, task_id):
        task = get_object_or_404(Task, id=task_id, is_deleted=False)
        organization = task.organization
        membership = get_member_membership(request, organization.id)
        
        is_admin_or_owner = membership and membership.role in ['admin', 'owner']
        is_creator = task.created_by == request.user
        
        if not (is_admin_or_owner or is_creator):
            return Response({"detail": "Only admins, owners, or the task creator can change assignees."}, status=status.HTTP_403_FORBIDDEN)

        user_id = request.data.get('user_id')
        if user_id:
            from users.models import User
            user = get_object_or_404(User, id=user_id)
            # Verify target user is in the same organization
            is_member = OrganizationMembership.objects.filter(organization=organization, user=user, is_active=True).exists()
            if not is_member:
                return Response({"error": "Target user is not a member of this organization."}, status=status.HTTP_400_BAD_REQUEST)
            task.assignee = user
        else:
            task.assignee = None

        task.save(update_fields=['assignee'])
        return Response({"message": "Assignee updated successfully by administrator override."}, status=status.HTTP_200_OK)


class ManualScheduleView(APIView):
    """
    Endpoint for manually running task scheduling for a specific user or all users in an organization.

    Logic (same as automatic Celery scheduling):
      1. Get all pending tasks assigned to the selected member (or all members).
      2. Sort by priority: High → Medium → Low.
      3. For each task, check if it can fit in a single continuous working block in the next 7 working days.
      4. If it fits → set planned_start / planned_end, and set schedule_status to SCHEDULED. If not → leave it QUEUED.
      5. Already-scheduled tasks are never touched.

    Only accessible to organization Owners and Admins.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT},
        description=(
            "Manually run the priority-based, capacity-aware task scheduling algorithm "
            "for a specific member (or all members if user_id is not provided)."
        ),
    )
    def post(self, request, org_id, *args, **kwargs):
        # 1. Validate the calling user is a member of this org
        get_object_or_404(Organization, id=org_id)
        membership = get_member_membership(request, org_id)
        if not membership:
            return Response(
                {"error": "You are not a member of this organization."},
                status=status.HTTP_403_FORBIDDEN,
                )

        user_id = request.data.get("user_id")
        is_admin_or_owner = membership.role in ['owner', 'admin']

        if not is_admin_or_owner:
            if user_id and str(user_id) != str(request.user.id):
                return Response(
                    {"error": "Employees can only schedule their own tasks."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            user_id = request.user.id
        elif not user_id:
            # If admin/owner and no user_id is provided, we default to scheduling for all members.
            pass

        from tasks.services.scheduler import schedule_tasks_for_assignee
        from organizations.models import OrganizationMembership

        if user_id:
            # Check user is an active member
            is_member = OrganizationMembership.objects.filter(
                organization_id=org_id,
                user_id=user_id,
                is_active=True
            ).exists()
            if not is_member:
                return Response({"error": "Selected user is not an active member of this organization."}, status=status.HTTP_400_BAD_REQUEST)
            
            scheduled = schedule_tasks_for_assignee(user_id, org_id)
            scheduled_data = [{
                "task_id": str(t.id),
                "task_title": t.title,
                "planned_start": t.planned_start.isoformat() if t.planned_start else None,
                "planned_end": t.planned_end.isoformat() if t.planned_end else None,
                "schedule_status": t.schedule_status,
            } for t in scheduled]
            
            return Response({
                "message": f"Successfully scheduled {len(scheduled)} tasks for the assignee.",
                "scheduled": scheduled_data
            }, status=status.HTTP_200_OK)
        else:
            # Schedule for all active members
            memberships = OrganizationMembership.objects.filter(
                organization_id=org_id,
                is_active=True
            ).select_related('user')
            
            total_scheduled = 0
            results = []
            for mem in memberships:
                scheduled = schedule_tasks_for_assignee(mem.user_id, org_id)
                total_scheduled += len(scheduled)
                results.extend([{
                    "task_id": str(t.id),
                    "task_title": t.title,
                    "assignee_email": mem.user.email,
                    "planned_start": t.planned_start.isoformat() if t.planned_start else None,
                    "planned_end": t.planned_end.isoformat() if t.planned_end else None,
                    "schedule_status": t.schedule_status,
                } for t in scheduled])
                
            return Response({
                "message": f"Successfully scheduled {total_scheduled} tasks for all active members.",
                "scheduled": results
            }, status=status.HTTP_200_OK)


from tasks.services import get_schedule_preview

class SchedulePreviewView(APIView):
    """
    Preview the next available time slot for a task.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=OpenApiTypes.OBJECT,
        responses={200: OpenApiTypes.OBJECT},
        description="Preview available time slot based on assignee and estimated hours."
    )
    def post(self, request, org_id):
        import json, traceback
        from django.utils import timezone
        
        log_data = {
            "timestamp": timezone.now().isoformat(),
            "org_id": str(org_id),
            "data": request.data,
            "headers": {k: v for k, v in request.META.items() if isinstance(v, str)},
            "status": None,
            "response": None,
            "error": None,
            "traceback": None
        }

        try:
            assignee_id = request.data.get('assignee')
            estimated_hours = request.data.get('estimated_hours')
            
            if not estimated_hours:
                log_data["status"] = 400
                log_data["error"] = "estimated_hours is required."
                with open("c:\\Users\\saura\\ParseOps\\backend\\debug_requests.txt", "a") as f:
                    f.write(json.dumps(log_data) + "\n")
                return Response({"error": "estimated_hours is required."}, status=400)
                
            try:
                estimated_hours = float(estimated_hours)
            except ValueError:
                log_data["status"] = 400
                log_data["error"] = "estimated_hours must be a number."
                with open("c:\\Users\\saura\\ParseOps\\backend\\debug_requests.txt", "a") as f:
                    f.write(json.dumps(log_data) + "\n")
                return Response({"error": "estimated_hours must be a number."}, status=400)

            task_id = request.data.get('task_id')
            start_search_from_raw = request.data.get('start_search_from')
            
            from django.utils.dateparse import parse_datetime
            start_search_from = parse_datetime(start_search_from_raw) if start_search_from_raw else None

            # If task_id is provided but no new start time was provided by the frontend,
            # use the task's existing planned_start as the anchor point.
            if task_id and not start_search_from:
                try:
                    from tasks.models import Task
                    task = Task.objects.get(id=task_id, organization_id=org_id)
                    start_search_from = task.planned_start
                except Exception:
                    pass

            # Get next available slot preview
            preview_res = get_schedule_preview(
                assignee_id=assignee_id, 
                estimated_hours=estimated_hours, 
                org_id=org_id,
                start_search_from=start_search_from,
                exclude_task_id=task_id
            )

            # Convert datetimes to ISO strings for JSON response
            if preview_res.get("planned_start") and not isinstance(preview_res["planned_start"], str):
                preview_res["planned_start"] = preview_res["planned_start"].isoformat()
            if preview_res.get("planned_end") and not isinstance(preview_res["planned_end"], str):
                preview_res["planned_end"] = preview_res["planned_end"].isoformat()
            
            if preview_res.get("segments"):
                for seg in preview_res["segments"]:
                    if not isinstance(seg["start"], str):
                        seg["start"] = seg["start"].isoformat()
                    if not isinstance(seg["end"], str):
                        seg["end"] = seg["end"].isoformat()

            log_data["status"] = 200
            log_data["response"] = preview_res
            with open("c:\\Users\\saura\\ParseOps\\backend\\debug_requests.txt", "a") as f:
                f.write(json.dumps(log_data, default=str) + "\n")
            return Response(preview_res, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            log_data["status"] = 500
            log_data["error"] = str(e)
            log_data["traceback"] = tb
            try:
                with open("c:\\Users\\saura\\ParseOps\\backend\\debug_requests.txt", "a") as f:
                    f.write(json.dumps(log_data, default=str) + "\n")
            except Exception:
                pass
            return Response({"error": "Failed to calculate schedule preview. Please try again."}, status=500)

class RunSchedulerView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasTaskPermissions]

    @extend_schema(request=None, responses={200: OpenApiTypes.OBJECT})
    def post(self, request, org_slug):
        from organizations.models import Organization
        from tasks.models import Task
        from tasks.services.scheduler import schedule_tasks_for_assignee

        try:
            org = Organization.objects.get(slug=org_slug)
            
            # Find all users in the org that have QUEUED tasks
            assignee_ids = Task.objects.filter(
                organization=org,
                schedule_status='QUEUED',
                status__in=['todo', 'in_progress'],
                is_deleted=False,
                assignee__isnull=False
            ).values_list('assignee_id', flat=True).distinct()

            scheduled_count = 0
            for assignee_id in assignee_ids:
                scheduled_tasks = schedule_tasks_for_assignee(assignee_id, org.id)
                if scheduled_tasks:
                    scheduled_count += len(scheduled_tasks)
            
            return Response({"message": f"Scheduler run successfully. {scheduled_count} tasks scheduled."}, status=200)
        except Organization.DoesNotExist:
            return Response({"error": "Organization not found."}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


import csv
from django.contrib.auth import get_user_model
User = get_user_model()

class ImportTasksCSVView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasTaskPermissions]
    parser_classes = [MultiPartParser]

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {"file": {"type": "string", "format": "binary"}}
            }
        },
        responses={200: OpenApiTypes.OBJECT}
    )
    def post(self, request, org_slug):
        from organizations.models import Organization
        from tasks.models import Task
        
        if 'file' not in request.FILES:
            return Response({"error": "No file uploaded."}, status=400)
            
        file = request.FILES['file']
        if not file.name.endswith('.csv'):
            return Response({"error": "Only CSV files are allowed."}, status=400)
            
        try:
            org = Organization.objects.get(slug=org_slug)
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            
            created_count = 0
            scheduled_count = 0
            queued_count = 0
            
            for row in reader:
                title = row.get('Title', '').strip()
                if not title:
                    continue
                
                description = row.get('Description', '').strip()
                priority = row.get('Priority', 'medium').lower()
                if priority not in ['low', 'medium', 'high']:
                    priority = 'medium'
                    
                est_hours_raw = row.get('Est_Hours', '').strip()
                try:
                    est_hours = float(est_hours_raw) if est_hours_raw else 1.0
                except ValueError:
                    est_hours = 1.0
                
                assignee_email = row.get('Assignee_Email', '').strip()
                assignee = None
                if assignee_email:
                    assignee = User.objects.filter(email=assignee_email).first()
                if not assignee:
                    assignee = request.user
                    
                task = Task.objects.create(
                    organization=org,
                    title=title,
                    description=description,
                    priority=priority,
                    estimated_hours=est_hours,
                    assignee=assignee,
                    created_by=request.user
                )
                
                # Run through normal task creation logic
                task = apply_automatic_task_schedule(task)
                
                created_count += 1
                if task.schedule_status == 'SCHEDULED':
                    scheduled_count += 1
                else:
                    queued_count += 1
                    
            return Response({
                "message": f"Successfully imported {created_count} tasks.",
                "scheduled_count": scheduled_count,
                "queued_count": queued_count
            }, status=200)
            
        except Exception as e:
            return Response({"error": f"Failed to process CSV: {str(e)}"}, status=500)
