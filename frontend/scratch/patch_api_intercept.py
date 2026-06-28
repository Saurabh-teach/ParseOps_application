import re

with open('c:/Users/saura/ParseOps/frontend/src/api.js', 'r', encoding='utf-8') as f:
    content = f.read()

target = """    // Check if the user lost access to the organization (e.g. removed by owner)
    if (error.response?.status === 403 || error.response?.status === 404) {
      if (originalRequest.url && (originalRequest.url.includes('/api/dashboard/workspace-apps') || originalRequest.url.includes('/api/organizations/'))) {
        window.dispatchEvent(new Event('workspace_access_lost'));
      }
    }"""

replacement = """    // Check if the user lost access to the organization (e.g. removed by owner)
    const errDetail = error.response?.data?.detail || error.response?.data?.error || "";
    const isRemovalError = 
      errDetail === "You are not an active member of this organization." ||
      errDetail === "You are not a member of this organization." ||
      errDetail === "User is not a member of this organization.";
      
    if (error.response?.status === 403 || error.response?.status === 404) {
      if (
        isRemovalError || 
        (error.response?.status === 404 && originalRequest.url && originalRequest.url.includes('/api/organizations/')) ||
        (error.response?.status === 403 && originalRequest.url && originalRequest.url.includes('/api/analytics/team/'))
      ) {
        window.dispatchEvent(new Event('workspace_access_lost'));
      }
    }"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/frontend/src/api.js', 'w', encoding='utf-8') as f:
    f.write(content)
print("api.js patched to handle workspace access lost robustly.")
