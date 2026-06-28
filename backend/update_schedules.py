import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import UserWorkingSchedule

updated = UserWorkingSchedule.objects.filter(work_end_time='18:00:00').update(work_end_time='19:00:00')
print(f'Updated {updated} records')
