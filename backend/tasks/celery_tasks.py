"""
tasks/celery_tasks.py
======================
Celery tasks for the tasks app.

Contains:
  - auto_schedule_all_users(): Periodic task that runs every 30 minutes
    and applies the simple scheduling algorithm for every user
    across all active organizations.

How to run:
  # Terminal 1 – Start the Celery worker (processes tasks)
  celery -A config worker --loglevel=info

  # Terminal 2 – Start Celery Beat (triggers scheduled tasks on time)
  celery -A config beat --loglevel=info

  # Optional: Run worker + beat together (development only)
  celery -A config worker --beat --loglevel=info
"""

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='tasks.celery_tasks.auto_schedule_all_users')
def auto_schedule_all_users(self):
    """
    Automatic Scheduling Task – runs every 30 minutes via Celery Beat.

    Calls manual_schedule(user_id, organization_id) for each active member
    of all active organizations.
    """
    # Import here to avoid circular imports at module load time
    from organizations.models import Organization, OrganizationMembership
    from tasks.services.scheduler import schedule_tasks_for_assignee

    logger.info("[auto_schedule_all_users] ⏰ Celery Beat triggered auto-scheduling...")

    total_users_processed = 0
    errors = []

    # 1. Get all active organizations
    organizations = Organization.objects.filter(is_active=True)
    logger.info(f"[auto_schedule_all_users] Found {organizations.count()} active organization(s).")

    for org in organizations:
        # Get all active memberships
        memberships = OrganizationMembership.objects.filter(
            organization=org,
            is_active=True
        ).select_related('user')
        
        logger.info(f"[auto_schedule_all_users] Processing org '{org.name}' with {memberships.count()} active member(s).")
        
        for membership in memberships:
            try:
                schedule_tasks_for_assignee(assignee_id=membership.user.id, org_id=org.id)
                total_users_processed += 1
            except Exception as exc:
                error_msg = f"Error scheduling for user {membership.user.email} in org {org.name}: {exc}"
                logger.error(f"[auto_schedule_all_users] ❌ {error_msg}")
                errors.append(error_msg)


    summary = {
        'total_users_processed': total_users_processed,
        'errors': errors,
    }

    logger.info(
        f"[auto_schedule_all_users] ✅ Done. "
        f"Users processed: {total_users_processed}, "
        f"Errors: {len(errors)}"
    )

    return summary
