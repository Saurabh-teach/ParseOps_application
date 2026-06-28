import re

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

target = """  useEffect(() => {

    // Listen for Service Worker messages"""

replacement = """  useEffect(() => {
    const handleWorkspaceLost = () => {
      setSelectedOrg(null);
      alert('You have lost access to this workspace. You are no longer a member.');
      getOrganizations().then(orgs => setOrganizations(orgs)).catch(() => {});
    };
    window.addEventListener('workspace_access_lost', handleWorkspaceLost);

    // Listen for Service Worker messages"""

content = content.replace(target, replacement)

# also need to remove event listener
target2 = """      navigator.serviceWorker.addEventListener('message', (event) => {

        if (event.data && event.data.type === 'PUSH_NOTIFICATION') {

          setPushToast({ title: event.data.title, body: event.data.body });

          // Auto-hide after 6 seconds

          setTimeout(() => setPushToast(null), 6000);

        }

      });

    }

  }, []);"""

replacement2 = """      navigator.serviceWorker.addEventListener('message', (event) => {

        if (event.data && event.data.type === 'PUSH_NOTIFICATION') {

          setPushToast({ title: event.data.title, body: event.data.body });

          // Auto-hide after 6 seconds

          setTimeout(() => setPushToast(null), 6000);

        }

      });

    }
    return () => window.removeEventListener('workspace_access_lost', handleWorkspaceLost);

  }, []);"""

content = content.replace(target2, replacement2)

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("App.jsx patched for workspace lost event")
