import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from datetime import datetime
from django.utils import timezone
from tasks.services.scheduler import get_next_available_slot
from users.models import User
import time

print("Testing get_next_available_slot...")
user = User.objects.first()
if user:
    start = time.time()
    try:
        start_dt, end_dt = get_next_available_slot(user.id, 5.0)
        print(f"Result: {start_dt} to {end_dt}")
        print(f"Time taken: {time.time() - start:.2f}s")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("No user found")
