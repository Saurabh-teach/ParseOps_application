import re

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """        # "direct there crediatial remove in database" 
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
        logger.info(f"User {user_email} removed from org {org.name}. Login credentials disabled: {active_orgs_count == 0}. Logged in Workspace History.")"""

replacement = """        # As requested: he only login in there login password connot access workspace okay
        # We do NOT disable user.is_active, so they can still log in but will see no workspace.
        user = membership.user
        
        # Add to python logs
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"User {user_email} removed from org {org.name}. Logged in Workspace History.")"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("organizations/views.py patched to NOT disable login credentials")
