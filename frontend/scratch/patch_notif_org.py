import re

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

fetch_notif_block = """  const fetchNotifications = async (memberId = null) => {
    try {
      const currentOrgSlug = localStorage.getItem('selectedOrgSlug') || '';
      const data = await getNotifications(currentOrgSlug, memberId);
      setNotifications(data);
    } catch (err) {
      console.error('Failed to fetch notifications:', err);
    }
  };"""

new_fetch_notif_block = """  const fetchNotifications = async (memberId = null) => {
    try {
      const currentOrgSlug = selectedOrg?.name || '';
      const data = await getNotifications(currentOrgSlug, memberId);
      setNotifications(data);
    } catch (err) {
      console.error('Failed to fetch notifications:', err);
    }
  };"""

if "selectedOrg?.name" not in content.split("fetchNotifications")[1][:200]:
    content = content.replace(fetch_notif_block, new_fetch_notif_block)
    with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
        
print("App.jsx patched for selectedOrg.name")
