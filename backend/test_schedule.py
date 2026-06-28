import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parseops.settings')
django.setup()

with open('test_out.txt', 'w') as f:
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.filter(email='bhangalesaurabh20+mem505@gmail.com').first()
        if user:
            f.write(f"User found: {user.id}\n")
            f.write(f"Has attr: {hasattr(user, 'working_schedule')}\n")
            if hasattr(user, 'working_schedule'):
                f.write(f"Schedule: {getattr(user.working_schedule, 'work_start_time', None)}\n")
        else:
            f.write("User not found\n")
    except Exception as e:
        f.write(f"Error: {e}\n")
