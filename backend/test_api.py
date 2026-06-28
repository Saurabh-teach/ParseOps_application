import urllib.request
import json
import uuid

# Find the exact assignee id from the debug log
with open("debug_requests.txt", "r") as f:
    for line in f:
        data = json.loads(line)
        if "assignee" in data.get("data", {}):
            assignee_id = data["data"]["assignee"]
            org_id = data["org_id"]
            break

print(f"Testing assignee {assignee_id} in org {org_id}")

req = urllib.request.Request(f"http://127.0.0.1:8000/api/organizations/{org_id}/tasks/schedule-preview/",
    data=json.dumps({
        "assignee": assignee_id,
        "estimated_hours": 1
    }).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
try:
    with urllib.request.urlopen(req) as response:
        print(response.read().decode())
except Exception as e:
    print(e)
