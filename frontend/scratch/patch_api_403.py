import re

with open('c:/Users/saura/ParseOps/frontend/src/api.js', 'r', encoding='utf-8') as f:
    content = f.read()

target = """    }
    return Promise.reject(error);
  }
);"""

replacement = """    }
    
    // Check if the user lost access to the organization (e.g. removed by owner)
    if (error.response?.status === 403 || error.response?.status === 404) {
      if (originalRequest.url && (originalRequest.url.includes('/api/dashboard/workspace-apps') || originalRequest.url.includes('/api/organizations/'))) {
        window.dispatchEvent(new Event('workspace_access_lost'));
      }
    }
    
    return Promise.reject(error);
  }
);"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/frontend/src/api.js', 'w', encoding='utf-8') as f:
    f.write(content)
print("api.js patched for 403/404 event")
