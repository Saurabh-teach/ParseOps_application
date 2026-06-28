import logging
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification

logger = logging.getLogger(__name__)
User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
#  Internal email helper
# ─────────────────────────────────────────────────────────────────────────────

def _format_user_name(user):
    if user and (user.first_name or user.last_name):
        return f"{user.first_name} {user.last_name}".strip()
    return ""

def _format_user_display(user):
    name = _format_user_name(user)
    if name:
        return f"{name} ({user.email})"
    return user.email

import threading

def _send_email_async(subject, body_html, to_email):
    try:
        send_mail(
            subject=subject,
            message=body_html,          # plain-text fallback
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False,
            html_message=body_html,     # rich HTML version
        )
        logger.info(f"Email sent to {to_email}: {subject}")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")

def _send_email(subject, body_html, to_email):
    """
    Sends a branded ParseOps email asynchronously using threading.
    Falls back silently so that notification creation never crashes.
    """
    thread = threading.Thread(target=_send_email_async, args=(subject, body_html, to_email))
    thread.daemon = True
    thread.start()
    return True


def _build_email(title, greeting, body_lines, action_url=None, action_label=None):
    """
    Builds a clean, branded HTML email body.
    """
    action_block = ""
    if action_url and action_label:
        action_block = f"""
        <div style="text-align:center;margin:32px 0;">
          <a href="{action_url}"
             style="background:#6366f1;color:#fff;padding:12px 28px;
                    border-radius:8px;font-weight:700;font-size:0.95rem;
                    text-decoration:none;display:inline-block;">
            {action_label}
          </a>
        </div>"""

    body_text = "".join(f"<p style='margin:8px 0;color:#475569;font-size:0.95rem;line-height:1.6;'>{l}</p>" for l in body_lines)

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family:'Inter',Arial,sans-serif;background:#f8fafc;padding:0;margin:0;">
      <div style="max-width:520px;margin:40px auto;background:#fff;
                  border-radius:16px;border:1px solid #e2e8f0;
                  box-shadow:0 4px 24px rgba(0,0,0,0.07);overflow:hidden;">
        <!-- Header -->
        <div style="background:linear-gradient(135deg,#6366f1,#818cf8);
                    padding:28px 32px;text-align:center;">
          <span style="font-size:1.4rem;font-weight:800;color:#fff;
                       letter-spacing:-0.02em;">ParseOps</span>
        </div>
        <!-- Body -->
        <div style="padding:32px;">
          <h2 style="margin:0 0 12px;font-size:1.15rem;font-weight:700;color:#0f172a;">
            {title}
          </h2>
          <p style="margin:0 0 16px;color:#64748b;font-size:0.9rem;">{greeting}</p>
          {body_text}
          {action_block}
          <hr style="border:none;border-top:1px solid #f1f5f9;margin:28px 0;">
          <p style="font-size:0.78rem;color:#94a3b8;text-align:center;margin:0;">
            © 2025 ParseOps · You received this because you're a member of a workspace.
          </p>
        </div>
      </div>
    </body>
    </html>
    """


# ─────────────────────────────────────────────────────────────────────────────
#  Notification creators  (in-app  +  email)
# ─────────────────────────────────────────────────────────────────────────────

def create_join_request_notification(join_request):
    """
    Triggers when a user requests to join an organization.
    • Creates in-app notifications for admins/owners.
    • Sends a real email to each admin/owner.
    """
    from organizations.models import Membership
    org = join_request.organization
    requester = join_request.user
    requester_display = _format_user_display(requester)
    requester_name = _format_user_name(requester)

    admins = Membership.objects.filter(
        organization=org, role__in=['owner', 'admin']
    ).select_related('user')

    notifications = []
    for admin_membership in admins:
        admin_user = admin_membership.user
        if admin_user == requester:
            continue
            
        admin_name = _format_user_name(admin_user)
        greeting = f"Hello {admin_name}," if admin_name else f"Hello {admin_user.email},"

        title = f"New Join Request: {org.name}"
        message = (
            f"{requester_display} requested to join {org.name} "
            f"as {join_request.requested_role}."
        )
        if join_request.message:
            message += f' Message: "{join_request.message}"'

        from notifications.services import NotificationService
        NotificationService.send_notification(
            recipient=admin_user,
            title=title,
            message=message,
            n_type='join_request',
            organization=org,
            data={
                'organization_id': str(org.id),
                'join_request_id': str(join_request.id),
                'requester_email': requester.email,
                'requested_role': join_request.requested_role,
            }
        )
        
        try:
            from notifications.webpush import send_web_push
            send_web_push(admin_user, title, message)
        except Exception as e:
            logger.error(f"Failed to send web push for join request: {e}")

        # ── Real email to the admin / owner ──────────────────────────────
        body_lines = []
        if requester_name:
            body_lines.append(f"<strong>{requester_name}</strong> <span style='font-size:0.85em;color:#64748b;'>({requester.email})</span> has requested to join <strong>{org.name}</strong> as <em>{join_request.requested_role}</em>.")
        else:
            body_lines.append(f"<strong>{requester.email}</strong> has requested to join <strong>{org.name}</strong> as <em>{join_request.requested_role}</em>.")
            
        if join_request.message:
            body_lines.append(f"Their message: <em>\"{join_request.message}\"</em>")
        body_lines.append(
            "Log in to ParseOps and navigate to <strong>Permissions</strong> "
            "to approve or deny this request."
        )

        html = _build_email(
            title=f"Join Request: {org.name}",
            greeting=greeting,
            body_lines=body_lines,
            action_url="http://localhost:5173",
            action_label="Review Request →",
        )
        _send_email(
            subject=f"New Join Request - {org.name}",
            body_html=html,
            to_email=admin_user.email,
        )

    logger.info(f"Created join request notifications for {org.name}")


def create_join_request_reviewed_notification(join_request):
    """
    Triggers when an admin approves or denies a join request.
    • Creates in-app notification for the requester.
    • Sends a real email to the requester.
    """
    org = join_request.organization
    requester = join_request.user
    status = join_request.status     # 'approved' or 'denied'
    status_text = "approved" if status == 'approved' else "denied"

    title = f"Join Request {status.capitalize()}: {org.name}"
    message = f"Your request to join workspace {org.name} has been {status_text}."

    from notifications.services import NotificationService
    NotificationService.send_notification(
        recipient=requester,
        title=title,
        message=message,
        n_type=f"join_request_{status}",
        organization=org,
        data={
            'organization_id': str(org.id),
            'join_request_id': str(join_request.id),
            'status': status,
        }
    )

    # ── Real email to the requester ───────────────────────────────────────
    if status == 'approved':
        body_lines = [
            f"Great news! Your request to join <strong>{org.name}</strong> "
            f"has been <strong style='color:#059669;'>approved</strong>.",
            "You can now log in to ParseOps and enter the workspace.",
        ]
        action_label = "Enter Workspace →"
        color_word = "<span style='color:#059669;font-weight:700;'>Approved ✓</span>"
    else:
        body_lines = [
            f"Unfortunately, your request to join <strong>{org.name}</strong> "
            f"has been <strong style='color:#ef4444;'>denied</strong>.",
            "You may contact the workspace admin for more information.",
        ]
        action_label = "Go to ParseOps →"
        color_word = "<span style='color:#ef4444;font-weight:700;'>Denied ✗</span>"

    body_lines.insert(0, f"Status: {color_word}")

    html = _build_email(
        title=title,
        greeting=f"Hello {requester.email},",
        body_lines=body_lines,
        action_url="http://localhost:5173",
        action_label=action_label,
    )
    _send_email(
        subject=f"[ParseOps] Your join request for {org.name} was {status_text}",
        body_html=html,
        to_email=requester.email,
    )

    logger.info(f"Created join request reviewed ({status_text}) notification for {requester.email}")


def create_invitation_notification(invitation, temp_password=None):
    """
    Triggers when a member is invited.
    • Creates in-app notification for the invited user (if registered).
    • Sends a real email to the invited address regardless.
    """
    org = invitation.organization
    email = invitation.email
    inviter = invitation.invited_by
    inviter_display = _format_user_display(inviter)
    inviter_name = _format_user_name(inviter) or inviter.email

    invited_user = User.objects.filter(email__iexact=email).first()
    invited_name = _format_user_name(invited_user) if invited_user else ""
    greeting = f"Hello {invited_name}," if invited_name else f"Hello {email},"

    if invited_user:
        title = f"Invitation to join: {org.name}"
        message = (
            f"{inviter_display} invited you to join the workspace "
            f"{org.name} as {invitation.role}."
        )
        if invitation.message:
            message += f' Message: "{invitation.message}"'

        from notifications.services import NotificationService
        NotificationService.send_notification(
            recipient=invited_user,
            title=title,
            message=message,
            n_type='invitation',
            organization=org,
            data={
                'organization_id': str(org.id),
                'invitation_id': str(invitation.id),
                'inviter_email': inviter.email,
                'role': invitation.role,
            }
        )
        logger.info(f"Created invitation notification for existing user: {email}")

    # ── Real email to the invited address (registered or not) ────────────
    body_lines = []
    
    if _format_user_name(inviter):
        body_lines.append(f"<strong>{_format_user_name(inviter)}</strong> <span style='font-size:0.85em;color:#64748b;'>({inviter.email})</span> has invited you to join <strong>{org.name}</strong> on ParseOps as <em>{invitation.role}</em>.")
    else:
        body_lines.append(f"<strong>{inviter.email}</strong> has invited you to join <strong>{org.name}</strong> on ParseOps as <em>{invitation.role}</em>.")

    if invitation.message:
        body_lines.append(f"Personal message: <em>\"{invitation.message}\"</em>")

    if temp_password:
        body_lines.append(
            f"An account has been automatically created for you.<br/>"
            f"<strong>Email:</strong> {email}<br/>"
            f"<strong>Temporary Password:</strong> {temp_password}<br/>"
            f"Note: You will be required to change your password upon your first login."
        )

    # Secure Accept Link
    action_url = f"http://localhost:5173/login?token={invitation.token}"

    if invited_user and not temp_password:
        body_lines.append(
            "Log in to ParseOps and accept the invitation from your "
            "<strong>Notifications</strong> panel or use the link below."
        )
        action_label = "Open ParseOps & Accept →"
    else:
        body_lines.append(
            "Use the link below to log in and accept your invitation."
        )
        action_label = "Log In & Accept →"

    html = _build_email(
        title=f"You're invited to join {org.name}",
        greeting=greeting,
        body_lines=body_lines,
        action_url=action_url,
        action_label=action_label,
    )
    _send_email(
        subject=f"{inviter_name} invited you to join {org.name}",
        body_html=html,
        to_email=email,
    )


def process_pending_invitations_for_new_user(user):
    """
    Called when a new user registers.
    Checks for pending invitations and fires in-app notifications.
    """
    from organizations.models import OrganizationInvitation
    invitations = OrganizationInvitation.objects.filter(
        email__iexact=user.email, status='pending'
    )
    for invitation in invitations:
        create_invitation_notification(invitation)


def create_invitation_accepted_notification(invitation):
    """
    Triggers when a user accepts an invitation.
    • Creates in-app notification for the inviter.
    • Sends a confirmation email to the inviter.
    """
    inviter = invitation.invited_by
    org = invitation.organization

    title = f"Invitation Accepted: {org.name}"
    message = (
        f"User {invitation.email} has accepted your invitation "
        f"to join {org.name} as {invitation.role}."
    )

    from notifications.services import NotificationService
    NotificationService.send_notification(
        recipient=inviter,
        title=title,
        message=message,
        n_type='invitation_accepted',
        organization=org,
        data={
            'organization_id': str(org.id),
            'invitation_id': str(invitation.id),
            'invitee_email': invitation.email,
            'role': invitation.role,
        }
    )

    # ── Real email to the inviter ────────────────────────────────────────
    html = _build_email(
        title=title,
        greeting=f"Hello {inviter.email},",
        body_lines=[
            f"<strong>{invitation.email}</strong> has accepted your invitation "
            f"and is now a member of <strong>{org.name}</strong> "
            f"as <em>{invitation.role}</em>.",
            "Head to ParseOps to see your updated team.",
        ],
        action_url="http://localhost:5173",
        action_label="View Team →",
    )
    _send_email(
        subject=f"[ParseOps] {invitation.email} accepted your invitation to {org.name}",
        body_html=html,
        to_email=inviter.email,
    )
    logger.info(f"Created invitation accepted notification for {inviter.email}")


def create_invitation_declined_notification(invitation):
    """
    Triggers when a user declines an invitation.
    • Creates in-app notification for the inviter.
    • Sends a notification email to the inviter.
    """
    inviter = invitation.invited_by
    org = invitation.organization

    title = f"Invitation Declined: {org.name}"
    message = (
        f"User {invitation.email} has declined your invitation "
        f"to join {org.name}."
    )

    from notifications.services import NotificationService
    NotificationService.send_notification(
        recipient=inviter,
        title=title,
        message=message,
        n_type='invitation_declined',
        organization=org,
        data={
            'organization_id': str(org.id),
            'invitation_id': str(invitation.id),
            'invitee_email': invitation.email,
        }
    )

    # ── Real email to the inviter ────────────────────────────────────────
    html = _build_email(
        title=title,
        greeting=f"Hello {inviter.email},",
        body_lines=[
            f"<strong>{invitation.email}</strong> has declined your invitation "
            f"to join <strong>{org.name}</strong>.",
            "You can send a new invitation from the Members section if needed.",
        ],
        action_url="http://localhost:5173",
        action_label="Manage Members →",
    )
    _send_email(
        subject=f"[ParseOps] {invitation.email} declined your invitation to {org.name}",
        body_html=html,
        to_email=inviter.email,
    )
    logger.info(f"Created invitation declined notification for {inviter.email}")

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

    from notifications.services import NotificationService
    from notifications.webpush import send_web_push

    try:
        NotificationService.send_notification(
            recipient=inviter,
            title=title,
            message=message,
            n_type='invitation_accepted',
            organization=org,
            data={
                'organization_id': str(org.id),
                'invitee_email': user.email,
                'role': membership.role,
            }
        )
    except Exception as e:
        logger.error(f"Failed to create notification: {e}")

    try:
        send_web_push(inviter, title, message)
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

