import requests

url = "http://localhost:8000/api/token/"
login_data = {
    "email": "bhangalesaurabh20+owner@gmail.com",
    "password": "securepass123" # Wait! What was the password?
}
# Let's get the token using requests
try:
    resp = requests.post(url, json={"email": "bhangalesaurabh20+owner@gmail.com", "password": "securepass123"})
    token = resp.json().get("access")
except Exception as e:
    print("Login failed:", e)
    token = None

if token:
    headers = {"Authorization": f"Bearer {token}"}
    create_url = "http://localhost:8000/api/tasks/create/"
    task_payload = {
        "organization": "a902b370-1fac-4fd6-bde9-b6fd4978566e",
        "title": "API Client Auto-Scheduling Test",
        "description": "Verifying API creation auto scheduling",
        "priority": "high",
        "risk": "medium",
        "impact": 7,
        "estimated_hours": 3.0,
        "assignees": []
    }
    
    resp_create = requests.post(create_url, json=task_payload, headers=headers)
    print("API RESPONSE STATUS:", resp_create.status_code)
    print("API RESPONSE BODY:", resp_create.json())
else:
    print("Could not login to retrieve token.")
