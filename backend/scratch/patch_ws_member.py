import re

with open('c:/Users/saura/ParseOps/backend/chat/consumers.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """    def is_org_member(self, user, org_id):
        return OrganizationMembership.objects.filter(organization_id=org_id, user=user, is_active=True).exists()"""

replacement = """    @database_sync_to_async
    def is_org_member(self, user, org_id):
        return OrganizationMembership.objects.filter(organization_id=org_id, user=user, is_active=True).exists()"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/backend/chat/consumers.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("ChatConsumer is_org_member patched with @database_sync_to_async")
