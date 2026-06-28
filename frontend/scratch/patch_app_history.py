import re

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Add historyMemberFilter state
states_block = """  const [isOwner, setIsOwner] = useState(false);"""
new_states_block = """  const [isOwner, setIsOwner] = useState(false);
  const [historyMemberFilter, setHistoryMemberFilter] = useState('');"""
if "historyMemberFilter" not in content:
    content = content.replace(states_block, new_states_block)

# Add member dropdown to History Header
header_block = """                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                    <div>
                      <h2 className="section-title-premium" style={{ marginBottom: '0.25rem' }}>Workspace Hub History</h2>
                      <p style={{ fontSize: '0.9rem', color: '#64748b', margin: 0 }}>Review active audits, trace changes, or restore deleted objects in {selectedOrg?.name}</p>
                    </div>
                  </div>"""

new_header_block = """                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                    <div>
                      <h2 className="section-title-premium" style={{ marginBottom: '0.25rem' }}>Workspace Hub History</h2>
                      <p style={{ fontSize: '0.9rem', color: '#64748b', margin: 0 }}>Review active audits, trace changes, or restore deleted objects in {selectedOrg?.name}</p>
                    </div>
                    {isOwner && (
                        <select
                            value={historyMemberFilter}
                            onChange={async (e) => {
                                setHistoryMemberFilter(e.target.value);
                                const history = await getWorkspaceHistory(selectedOrg.id, e.target.value).catch(() => []);
                                setOrgHistory(history);
                            }}
                            style={{ padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', outline: 'none' }}
                        >
                            <option value="">All Members</option>
                            {members.map(m => (
                                <option key={m.user.id} value={m.user.id}>{m.user.email} ({m.role})</option>
                            ))}
                        </select>
                    )}
                  </div>"""

if "historyMemberFilter" not in content:
    content = content.replace(header_block, new_header_block)

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("App.jsx patched for history filter")
