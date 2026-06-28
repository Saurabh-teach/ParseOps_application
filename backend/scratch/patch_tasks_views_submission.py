import re

with open('c:/Users/saura/ParseOps/backend/tasks/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_view = """
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
"""

content += new_view

with open('c:/Users/saura/ParseOps/backend/tasks/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Added TaskSubmissionView to tasks/views.py")
