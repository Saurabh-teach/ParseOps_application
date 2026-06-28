import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User, UserWorkingSchedule

def run_backfill():
    users = User.objects.all()
    created_count = 0
    for user in users:
        schedule, created = UserWorkingSchedule.objects.get_or_create(user=user)
        if created:
            created_count += 1
    print(f"Backfilled schedules for {created_count} users.")

if __name__ == '__main__':
    run_backfill()
