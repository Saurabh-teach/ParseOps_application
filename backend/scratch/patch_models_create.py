import re

with open('c:/Users/saura/ParseOps/backend/organizations/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

clean_block = """    def clean(self):
        super().clean()
        if self.pk:
            old = OrganizationMembership.objects.get(pk=self.pk)
            # If demoting from owner or deactivating an owner
            if old.role == 'owner' and old.is_active:
                if self.role != 'owner' or not self.is_active:
                    owner_count = OrganizationMembership.objects.filter(
                        organization=self.organization, 
                        role='owner', 
                        is_active=True
                    ).exclude(pk=self.pk).count()
                    if owner_count == 0:
                        raise ValidationError("An organization must have at least one active owner.")"""

new_clean_block = """    def clean(self):
        super().clean()
        if not self._state.adding:
            try:
                old = OrganizationMembership.objects.get(pk=self.pk)
                # If demoting from owner or deactivating an owner
                if old.role == 'owner' and old.is_active:
                    if self.role != 'owner' or not self.is_active:
                        owner_count = OrganizationMembership.objects.filter(
                            organization=self.organization, 
                            role='owner', 
                            is_active=True
                        ).exclude(pk=self.pk).count()
                        if owner_count == 0:
                            raise ValidationError("An organization must have at least one active owner.")
            except OrganizationMembership.DoesNotExist:
                pass"""

content = content.replace(clean_block, new_clean_block)

with open('c:/Users/saura/ParseOps/backend/organizations/models.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("models.py patched for creation state")
