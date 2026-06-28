import django
import os
import sys

sys.path.append('c:/Users/saura/ParseOps/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.cache import cache
otp = cache.get("otp:login:bhangalesaurabh20+owner@gmail.com")
print(f"OTP: {otp}")
