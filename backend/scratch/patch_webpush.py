import re

with open('c:/Users/saura/ParseOps/backend/notifications/organization.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add send_web_push to create_join_request_notification
old_create_join = """        notifications.append(Notification(
            user=admin_user,
            title=title,
            message=message,
            notification_type='join_request',
            data={
                'organization_id': str(org.id),
                'join_request_id': str(join_request.id),
                'requester_email': requester.email,
                'requested_role': join_request.requested_role,
            }
        ))"""

new_create_join = """        notifications.append(Notification(
            user=admin_user,
            title=title,
            message=message,
            notification_type='join_request',
            data={
                'organization_id': str(org.id),
                'join_request_id': str(join_request.id),
                'requester_email': requester.email,
                'requested_role': join_request.requested_role,
            }
        ))
        
        try:
            from notifications.webpush import send_web_push
            send_web_push(admin_user, title, message)
        except Exception as e:
            logger.error(f"Failed to send web push for join request: {e}")"""

content = content.replace(old_create_join, new_create_join)

# Add send_web_push to create_join_request_reviewed_notification
old_reviewed = """    try:
        Notification.objects.create(
            user=requester,
            title=title,
            message=message,
            notification_type='join_request_reviewed',
            data={
                'organization_id': str(org.id),
                'status': join_request.status,
            }
        )
    except Exception as e:
        logger.error(f"Failed to create notification: {e}")"""

new_reviewed = """    try:
        Notification.objects.create(
            user=requester,
            title=title,
            message=message,
            notification_type='join_request_reviewed',
            data={
                'organization_id': str(org.id),
                'status': join_request.status,
            }
        )
    except Exception as e:
        logger.error(f"Failed to create notification: {e}")
        
    try:
        from notifications.webpush import send_web_push
        send_web_push(requester, title, message)
    except Exception as e:
        logger.error(f"Failed to send web push for join request review: {e}")"""

content = content.replace(old_reviewed, new_reviewed)

with open('c:/Users/saura/ParseOps/backend/notifications/organization.py', 'w', encoding='utf-8') as f:
    f.write(content)
