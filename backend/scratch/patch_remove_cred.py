import re

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """        user_email = membership.user.email
        # Hard delete the credential from the database as requested
        membership.delete()
        
        # Add to logs
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"CREDENTIAL REMOVED: User {user_email} was completely removed from organization {org.name} by {request.user.email}")
        
        # Send WebSocket signal to kick the user"""

replacement = """        user_email = membership.user.email
        
        # Soft delete membership so it STILL SHOWS UP in the Workspace History logs
        membership.is_active = False
        membership.save()
        
        # "direct there crediatial remove in database" 
        # Disable their user account entirely if they don't belong to any other active organizations
        user = membership.user
        active_orgs_count = OrganizationMembership.objects.filter(user=user, is_active=True).count()
        if active_orgs_count == 0:
            user.is_active = False
            user.set_unusable_password()
            user.save()
            
        # Add to python logs
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"User {user_email} removed from org {org.name}. Login credentials disabled: {active_orgs_count == 0}. Logged in Workspace History.")
        
        # Send WebSocket signal to kick the user"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("organizations/views.py patched to disable user credentials and keep history logs")
