import re
import os

# 1. Update models.py
with open('c:/Users/saura/ParseOps/backend/chat/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

model_block = """    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)"""
new_model_block = """    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    url_preview = models.JSONField(null=True, blank=True)"""
if "url_preview" not in content:
    content = content.replace(model_block, new_model_block)
    with open('c:/Users/saura/ParseOps/backend/chat/models.py', 'w', encoding='utf-8') as f:
        f.write(content)

# 2. Update serializers.py
with open('c:/Users/saura/ParseOps/backend/chat/serializers.py', 'r', encoding='utf-8') as f:
    content = f.read()

fields_block = """            'reply_to_preview', 'is_edited', 'is_deleted', 
            'created_at', 'updated_at', 'reactions', 'attachments'"""
new_fields_block = """            'reply_to_preview', 'is_edited', 'is_deleted', 'url_preview',
            'created_at', 'updated_at', 'reactions', 'attachments'"""
if "'url_preview'" not in content:
    content = content.replace(fields_block, new_fields_block)
    with open('c:/Users/saura/ParseOps/backend/chat/serializers.py', 'w', encoding='utf-8') as f:
        f.write(content)

print("models and serializers updated for url_preview")
