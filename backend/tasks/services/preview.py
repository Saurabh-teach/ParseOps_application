from datetime import datetime
from tasks.services.scheduler import get_next_available_slot
from tasks.services.calendar import to_org_tz
from organizations.models import Organization

def get_schedule_preview(assignee_id, estimated_hours: float, org_id, start_search_from: datetime = None, exclude_task_id=None):
    """
    Returns the preview of the next available slot for a task.
    Localizes outputs to organization timezone to prevent frontend substring parsing bugs.
    """
    from django.contrib.auth import get_user_model
    try:
        user = get_user_model().objects.get(id=assignee_id)
    except Exception:
        user = None

    segments = get_next_available_slot(
        assignee_id=assignee_id,
        duration_minutes=int(estimated_hours * 60),
        org_id=org_id,
        start_search_from=start_search_from,
        is_preview=True,
        user=user,
        exclude_task_id=exclude_task_id
    )
    
    if segments:
        try:
            org = Organization.objects.get(id=org_id)
            for seg in segments:
                seg["start"] = to_org_tz(seg["start"], org)
                seg["end"] = to_org_tz(seg["end"], org)
        except Exception:
            pass
            
        return {
            "planned_start": segments[0]["start"],
            "planned_end": segments[-1]["end"],
            "segments": segments,
            "message": "Available slot found."
        }
    else:
        return {
            "planned_start": None,
            "planned_end": None,
            "segments": [],
            "message": "Task will go to Queue Bucket (No available slots within the 7-day scheduling window)."
        }
