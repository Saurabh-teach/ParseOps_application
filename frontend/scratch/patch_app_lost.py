import re

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

target = """    const handleWorkspaceLost = () => {
      setSelectedOrg(null);
      alert('You are not a member of any organization.');
      getOrganizations().then(orgs => setOrganizations(orgs)).catch(() => {});
    };"""

replacement = """    const handleWorkspaceLost = () => {
      setSelectedOrg(null);
      sessionStorage.removeItem('selectedOrgId');
      setView('onboarding');
      alert('You are not a member of any organization.');
      getOrganizations().then(orgs => setOrganizations(orgs)).catch(() => {});
    };"""

content = content.replace(target, replacement)

# Also fix the crash on line 5168 just in case
target2 = """className={`dropdown-item ${org.id === selectedOrg.id ? 'active' : ''}`}"""
replacement2 = """className={`dropdown-item ${org.id === selectedOrg?.id ? 'active' : ''}`}"""
content = content.replace(target2, replacement2)

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("App.jsx patched to handle workspace lost and prevent crash")
