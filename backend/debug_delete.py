import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from tasks.models import Task
from tasks.views import SoftDeleteTaskView
from rest_framework.test import APIRequestFactory

User = get_user_model()

# Get user and task
user = User.objects.get(email='saurabhangale9332+test3@gmail.com')
task = Task.objects.filter(title='Build Swagger Documentation').first()

if not task:
    print("TASK NOT FOUND!")
    exit(1)

# Create request
factory = APIRequestFactory()
request = factory.delete(f'/api/tasks/{task.id}/soft-delete/')
request.user = user

# Instantiate view
view = SoftDeleteTaskView()
view.kwargs = {'task_id': str(task.id)}

print("=== RUNNING PERMISSION CHECKS ===")
print("User:", user.email)
print("Task Title:", task.title)
print("Task ID:", task.id, type(task.id))
print("Task Organization:", task.organization.name, task.organization.id)

# 1. IsAuthenticated
from rest_framework.permissions import IsAuthenticated
is_auth = IsAuthenticated()
print("IsAuthenticated.has_permission:", is_auth.has_permission(request, view))

# 2. IsOrganizationMember
from tasks.permissions import IsOrganizationMember
is_member = IsOrganizationMember()
has_perm = is_member.has_permission(request, view)
print("IsOrganizationMember.has_permission:", has_perm)
if has_perm:
    print("IsOrganizationMember.has_object_permission:", is_member.has_object_permission(request, view, task))

# 3. CanDeleteTask
from tasks.permissions import CanDeleteTask
can_delete = CanDeleteTask()
has_perm_del = can_delete.has_permission(request, view)
print("CanDeleteTask.has_permission:", has_perm_del)
if has_perm_del:
    print("CanDeleteTask.has_object_permission:", can_delete.has_object_permission(request, view, task))
