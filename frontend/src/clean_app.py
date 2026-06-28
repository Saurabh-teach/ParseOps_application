import re
import os

app_path = "c:/Users/saura/ParseOps/frontend/src/App.jsx"
with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

# Remove the Smart Suggestion Feature blocks
pattern = r"\{/\*\s*Commented:\s*Smart Suggestion Feature.*?\*/\}"
content = re.sub(pattern, "", content, flags=re.DOTALL)

# Remove specific console.logs
lines = content.split('\n')
new_lines = []
for line in lines:
    if "console.log('Web Push Subscription saved successfully.');" in line:
        continue
    if "console.log('SAML authentication successful, initializing session...');" in line:
        continue
    if "console.log('Workspaces fetched successfully:', allOrgs.length);" in line:
        continue
    if "console.log('Login OTP verified, fetching workspaces...');" in line:
        continue
    if "console.log(\"Opening Extension Modal for task:\", activeTask.id);" in line:
        continue
    if "console.log(\"TaskExtensionModal render" in line:
        continue
    new_lines.append(line)

with open(app_path, "w", encoding="utf-8") as f:
    f.write('\n'.join(new_lines))

print("Cleaned App.jsx")
