import os

app_path = r"d:\test_applications\backend\users\models.py"
with open(app_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# We know lines 180 to 350 (0-indexed) are duplicate.
# Wait, let's verify line contents first.
assert "def create_user(self" in lines[180]
assert "cancellation_reason = models.TextField" in lines[350]

# Delete those lines
del lines[180:351]

with open(app_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Fixed models.py duplicates")
