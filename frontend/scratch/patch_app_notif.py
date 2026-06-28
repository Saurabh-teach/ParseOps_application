import re

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Add notifMemberFilter state
states_block = """  const [historyMemberFilter, setHistoryMemberFilter] = useState('');"""
new_states_block = """  const [historyMemberFilter, setHistoryMemberFilter] = useState('');
  const [notifMemberFilter, setNotifMemberFilter] = useState('');"""
if "notifMemberFilter" not in content:
    content = content.replace(states_block, new_states_block)


# Update fetchNotifications function
fetch_notif_block = """  const fetchNotifications = async () => {
    try {
      const data = await getNotifications();
      setNotifications(data);
    } catch (err) {
      console.error('Failed to fetch notifications:', err);
    }
  };"""

new_fetch_notif_block = """  const fetchNotifications = async (memberId = null) => {
    try {
      const currentOrgSlug = localStorage.getItem('selectedOrgSlug') || '';
      const data = await getNotifications(currentOrgSlug, memberId);
      setNotifications(data);
    } catch (err) {
      console.error('Failed to fetch notifications:', err);
    }
  };"""

if "currentOrgSlug =" not in content:
    content = content.replace(fetch_notif_block, new_fetch_notif_block)

# Add dropdown to Notifications UI
header_block = """                  <div>
                    <h2 className="section-title-premium" style={{ marginBottom: '0.25rem' }}>Notification History</h2>
                    <p style={{ fontSize: '0.9rem', color: '#64748b', margin: 0 }}>View all your past and present notifications like a messenger</p>
                  </div>"""

new_header_block = """                  <div>
                    <h2 className="section-title-premium" style={{ marginBottom: '0.25rem' }}>Notification History</h2>
                    <p style={{ fontSize: '0.9rem', color: '#64748b', margin: 0 }}>View all your past and present notifications like a messenger</p>
                  </div>
                  {isOwner && (
                        <select
                            value={notifMemberFilter}
                            onChange={(e) => {
                                setNotifMemberFilter(e.target.value);
                                fetchNotifications(e.target.value);
                            }}
                            style={{ padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', outline: 'none', marginLeft: 'auto', marginRight: '1rem' }}
                        >
                            <option value="">All Members</option>
                            {members.map(m => (
                                <option key={m.user.id} value={m.user.id}>{m.user.email} ({m.role})</option>
                            ))}
                        </select>
                  )}"""

if "notifMemberFilter" not in content:
    content = content.replace(header_block, new_header_block)

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("App.jsx patched for notifications filter")
