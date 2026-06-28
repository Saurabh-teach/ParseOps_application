import re

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """    def get_queryset(self):
        # Return active public orgs OR orgs where user is an active member
        # (Exclude soft-deleted/inactive orgs unless they are the owner)
        return Organization.objects.filter(
            Q(is_active=True) & (Q(is_public=True) | Q(memberships__user=self.request.user))
        ).distinct().annotate(
            member_count=Count('memberships', filter=Q(memberships__is_active=True))
        )"""

replacement = """    def get_queryset(self):
        # Return active public orgs OR orgs where user is an active member
        # (Exclude soft-deleted/inactive orgs unless they are the owner)
        return Organization.objects.filter(
            Q(is_active=True) & (Q(is_public=True) | Q(memberships__user=self.request.user, memberships__is_active=True))
        ).distinct().annotate(
            member_count=Count('memberships', filter=Q(memberships__is_active=True))
        )"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("organizations/views.py patched to exclude soft-deleted memberships from queryset")
