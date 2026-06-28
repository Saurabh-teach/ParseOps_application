import re

with open('c:/Users/saura/ParseOps/backend/users/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

model_block = """class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)"""
new_model_block = """class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)"""
if "is_online =" not in content:
    content = content.replace(model_block, new_model_block)
    with open('c:/Users/saura/ParseOps/backend/users/models.py', 'w', encoding='utf-8') as f:
        f.write(content)
        
print("users/models.py patched for online status")
