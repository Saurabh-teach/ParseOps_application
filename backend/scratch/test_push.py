import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from notifications.webpush import send_web_push
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()

print("Found user:", user.email if user else "None")

try:
    send_web_push(user, "Test Title", "Test Body")
    print("Success without exceptions!")
except Exception as e:
    import traceback
    traceback.print_exc()
