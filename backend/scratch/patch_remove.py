import re

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """        membership.is_active = False
        membership.save()
        
        # Send WebSocket signal to kick the user"""

replacement = """        user_email = membership.user.email
        # Hard delete the credential from the database as requested
        membership.delete()
        
        # Add to logs
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"CREDENTIAL REMOVED: User {user_email} was completely removed from organization {org.name} by {request.user.email}")
        
        # Send WebSocket signal to kick the user"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("organizations/views.py patched to hard delete membership")
