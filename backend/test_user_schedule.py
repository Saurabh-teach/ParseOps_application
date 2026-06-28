import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

user = User.objects.first()
res = []
res.append(f"User: {user}")
res.append(f"Has working_schedule: {hasattr(user, 'working_schedule')}")
if hasattr(user, 'working_schedule'):
    res.append(f"Work Start: {user.working_schedule.work_start_time}")
    res.append(f"Work End: {user.working_schedule.work_end_time}")

with open("c:\\Users\\saura\\ParseOps\\backend\\test_out.txt", "w") as f:
    f.write("\n".join(res))
