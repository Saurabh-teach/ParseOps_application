def create_temp_password_accepted_notification(membership):
    """
    Triggers when a user logs in for the first time with a temporary password and changes it.
    • Creates in-app notification for the inviter.
    • Sends a web push notification.
    • Sends a confirmation email to the inviter.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    inviter = membership.invited_by
    if not inviter:
        return
        
    org = membership.organization
    user = membership.user

    title = f"Invitation Accepted: {org.name}"
    message = (
        f"User {user.email} has logged in and accepted your invitation "
        f"to join {org.name} as {membership.role}."
    )

    from notifications.models import Notification
    from notifications.webpush import send_webpush_notification

    try:
        Notification.objects.create(
            user=inviter,
            title=title,
            message=message,
            notification_type='invitation_accepted',
            data={
                'organization_id': str(org.id),
                'invitee_email': user.email,
                'role': membership.role,
            }
        )
    except Exception as e:
        logger.error(f"Failed to create notification: {e}")

    try:
        send_webpush_notification(inviter, title, message)
    except Exception as e:
        logger.error(f"Failed to send web push: {e}")

    # Real email to the inviter
    try:
        html = _build_email(
            title=title,
            greeting=f"Hello {inviter.email},",
            body_lines=[
                f"<strong>{user.email}</strong> has accepted your invitation "
                f"and is now fully active in <strong>{org.name}</strong> "
                f"as <em>{membership.role}</em>.",
                "Head to ParseOps to see your updated team.",
            ],
            action_url="http://localhost:5173",
            action_label="View Team →",
        )
        _send_email(
            subject=f"[ParseOps] {user.email} accepted your invitation to {org.name}",
            body_html=html,
            to_email=inviter.email,
        )
    except Exception as e:
        logger.error(f"Failed to send email notification: {e}")
        
    logger.info(f"Created temp password accepted notification for {inviter.email}")
