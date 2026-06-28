import re

with open('c:/Users/saura/ParseOps/backend/organizations/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

import_block = "from django.utils.text import slugify"
new_import_block = "from django.utils.text import slugify\nfrom django.core.exceptions import ValidationError"
if "from django.core.exceptions import ValidationError" not in content:
    content = content.replace(import_block, new_import_block)

methods_block = """    def __str__(self):
        return f"{self.user.email} in {self.organization.name} ({self.role})\"\"\""""

methods_to_replace = """    class Meta:
        db_table = 'org_membership'
        unique_together = ('organization', 'user')

    def __str__(self):
        return f"{self.user.email} in {self.organization.name} ({self.role})\""""

new_methods_block = """    class Meta:
        db_table = 'org_membership'
        unique_together = ('organization', 'user')

    def clean(self):
        super().clean()
        if self.pk:
            old = OrganizationMembership.objects.get(pk=self.pk)
            # If demoting from owner, or deactivating an owner
            if old.role == 'owner' and old.is_active:
                if self.role != 'owner' or not self.is_active:
                    owner_count = OrganizationMembership.objects.filter(
                        organization=self.organization, 
                        role='owner', 
                        is_active=True
                    ).exclude(pk=self.pk).count()
                    if owner_count == 0:
                        raise ValidationError("An organization must have at least one active owner.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.role == 'owner' and self.is_active:
            owner_count = OrganizationMembership.objects.filter(
                organization=self.organization, 
                role='owner', 
                is_active=True
            ).exclude(pk=self.pk).count()
            if owner_count == 0:
                raise ValidationError("Cannot delete the last active owner of an organization.")
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} in {self.organization.name} ({self.role})\""""

if "def clean" not in content.split("class OrganizationMembership")[1]:
    # Need to be careful with replace, use find
    start_meta = content.find("    class Meta:\n        db_table = 'org_membership'")
    end_str = content.find("class OrganizationJoinRequest", start_meta)
    
    if start_meta != -1 and end_str != -1:
        new_text = """    class Meta:
        db_table = 'org_membership'
        unique_together = ('organization', 'user')

    def clean(self):
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
                        raise ValidationError("An organization must have at least one active owner.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.role == 'owner' and self.is_active:
            owner_count = OrganizationMembership.objects.filter(
                organization=self.organization, 
                role='owner', 
                is_active=True
            ).exclude(pk=self.pk).count()
            if owner_count == 0:
                raise ValidationError("Cannot delete the last active owner of an organization.")
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} in {self.organization.name} ({self.role})\n\n"""
        
        content = content[:start_meta] + new_text + content[end_str:]
        with open('c:/Users/saura/ParseOps/backend/organizations/models.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("models.py patched")
    else:
        print("Could not find blocks")
