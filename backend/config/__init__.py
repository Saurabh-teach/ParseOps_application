"""
config/__init__.py
==================
This makes the Celery app available as `config.celery_app` and ensures
it is loaded when Django starts, so the @shared_task decorator works correctly.

IMPORTANT: This file MUST import the celery app at package load time.
"""

# Make the Celery app available at the top level of the config package
from .celery import app as celery_app

__all__ = ('celery_app',)
