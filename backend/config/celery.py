"""
Celery Application Configuration
==================================
This file sets up the Celery app for ParseOps.

How it works:
  - Celery reads configuration from Django settings (CELERY_* keys).
  - autodiscover_tasks() automatically finds tasks in every INSTALLED_APP's
    `celery_tasks.py` (or tasks.py) module.

Usage:
  Start worker:  celery -A config worker --loglevel=info
  Start beat:    celery -A config beat --loglevel=info
"""

import os
from celery import Celery

# Tell Celery which Django settings module to use
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create the Celery application
app = Celery('config')

# Load Celery config from Django settings, using the CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

from celery.schedules import crontab

# Auto-discover tasks from all INSTALLED_APPS
# Celery will look for a `celery_tasks.py` file in each app
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    'auto-schedule-every-30-mins': {
        'task': 'tasks.celery_tasks.auto_schedule_all_users',
        'schedule': crontab(minute='*/30'),
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """A simple debug task to verify Celery is working."""
    print(f'Request: {self.request!r}')
