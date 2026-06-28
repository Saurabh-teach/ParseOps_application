import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tasks.models import Task
from goals.models import Goals
from chat.models import ChatRoom, ChatParticipant

def backfill():
    print("Backfilling Goal Chats...")
    for goal in Goals.objects.all():
        room, created = ChatRoom.objects.get_or_create(
            organization=goal.organization,
            room_type='goal',
            goal=goal,
            defaults={'name': f"Goal: {goal.title}"}
        )
        if created:
            print(f"Created chat for Goal: {goal.title}")
        for assignee in goal.assignees.all():
            ChatParticipant.objects.get_or_create(room=room, user=assignee)

    print("Backfilling Task Chats...")
    for task in Task.objects.all():
        room, created = ChatRoom.objects.get_or_create(
            organization=task.organization,
            room_type='task',
            task=task,
            defaults={'name': f"Task: {task.title}"}
        )
        if created:
            print(f"Created chat for Task: {task.title}")
        if task.assignee:
            ChatParticipant.objects.get_or_create(room=room, user=task.assignee)
            
    print("Backfill complete.")

if __name__ == '__main__':
    backfill()
