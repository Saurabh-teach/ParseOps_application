import os
import re

app_jsx_path = r"d:\test_applications\frontend\src\App.jsx"

with open(app_jsx_path, 'r', encoding='utf-8') as f:
    content = f.read()

# BLOCK 1: Normalization
block1_search = """    // Normalize role for backend ('limited_member' and 'guest' map to 'member')
    let backendRole = inviteData.role;
    if (backendRole === 'limited_member' || backendRole === 'guest') {
      backendRole = 'member';
    }
    await inviteMember(selectedOrg.id, inviteData.email, backendRole, inviteData.message);"""

block1_replace = """    await inviteMember(selectedOrg.id, inviteData.email, inviteData.role, inviteData.message);"""

if block1_search in content:
    content = content.replace(block1_search, block1_replace)
    print("Replaced Block 1")
else:
    print("Could not find Block 1")

# BLOCK 2: Display
block2_search = """                  <div className="invite-role-title" style={{ fontSize: '0.85rem', fontWeight: 600, color: '#0f172a' }}>
                    {inviteData.role === 'admin' ? 'Admin' :
                      inviteData.role === 'limited_member' ? 'Limited Member' :
                        inviteData.role === 'guest' ? 'Guest' : 'Member'}
                  </div>
                  <div className="invite-role-desc" style={{ fontSize: '0.75rem', color: '#64748b', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '240px', marginTop: '1px' }}>
                    {inviteData.role === 'admin' && 'Can manage Spaces, People, Billing and other Workspace settings.'}
                    {inviteData.role === 'limited_member' && 'Can only access items shared with them.'}
                    {inviteData.role === 'guest' && "Can't use all features or be added to Spaces. Can only access items shared with them."}
                    {inviteData.role === 'member' && 'Can access all public items in your Workspace.'}
                  </div>"""

block2_replace = """                  <div className="invite-role-title" style={{ fontSize: '0.85rem', fontWeight: 600, color: '#0f172a' }}>
                    {inviteData.role === 'admin' ? 'Admin' :
                      inviteData.role === 'owner' ? 'Owner' : 'Member'}
                  </div>
                  <div className="invite-role-desc" style={{ fontSize: '0.75rem', color: '#64748b', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '240px', marginTop: '1px' }}>
                    {inviteData.role === 'owner' && 'Full access to all Workspace settings and billing.'}
                    {inviteData.role === 'admin' && 'Can manage Spaces, People, Billing and other Workspace settings.'}
                    {inviteData.role === 'member' && 'Can access all public items in your Workspace.'}
                  </div>"""

if block2_search in content:
    content = content.replace(block2_search, block2_replace)
    print("Replaced Block 2")
else:
    print("Could not find Block 2")

# BLOCK 3: Dropdown
block3_search = """                {/* Limited Member option */}
                <div
                  className={`invite-role-option ${inviteData.role === 'limited_member' ? 'selected' : ''}`}
                  onClick={() => { setInviteData({ ...inviteData, role: 'limited_member' }); setShowRoleDropdown(false); }}
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.6rem 1rem', cursor: 'pointer', borderLeft: inviteData.role === 'limited_member' ? '3px solid #6366f1' : '3px solid transparent', background: inviteData.role === 'limited_member' ? '#f8fafc' : 'transparent' }}
                >
                  <div className="invite-option-content" style={{ textAlign: 'left' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span className="invite-option-title" style={{ fontSize: '0.825rem', fontWeight: 600, color: '#1e293b' }}>Limited Member</span>
                      <span className="invite-option-badge" style={{ fontSize: '0.65rem', background: '#faf5ff', color: '#8b5cf6', border: '1px solid #ebd5ff', padding: '0.05rem 0.35rem', borderRadius: '4px', fontWeight: 500 }}>Chat Collaborator</span>
                    </div>
                    <div className="invite-option-desc" style={{ fontSize: '0.725rem', color: '#64748b', marginTop: '2px' }}>Can only access items shared with them.</div>
                  </div>
                  {inviteData.role === 'limited_member' && <span className="invite-option-checkmark" style={{ color: '#6366f1', fontSize: '0.85rem', fontWeight: 'bold' }}>✓</span>}
                </div>
                {/* Guest option */}
                <div
                  className={`invite-role-option ${inviteData.role === 'guest' ? 'selected' : ''}`}
                  onClick={() => { setInviteData({ ...inviteData, role: 'guest' }); setShowRoleDropdown(false); }}
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.6rem 1rem', cursor: 'pointer', borderLeft: inviteData.role === 'guest' ? '3px solid #6366f1' : '3px solid transparent', background: inviteData.role === 'guest' ? '#f8fafc' : 'transparent' }}
                >
                  <div className="invite-option-content" style={{ textAlign: 'left' }}>
                    <span className="invite-option-title" style={{ fontSize: '0.825rem', fontWeight: 600, color: '#1e293b' }}>Guest</span>
                    <div className="invite-option-desc" style={{ fontSize: '0.725rem', color: '#64748b', marginTop: '2px' }}>Can't use all features or be added to Spaces. Can only access items shared with them.</div>
                  </div>
                  {inviteData.role === 'guest' && <span className="invite-option-checkmark" style={{ color: '#6366f1', fontSize: '0.85rem', fontWeight: 'bold' }}>✓</span>}
                </div>
                {/* Admin option */}
                <div
                  className={`invite-role-option ${inviteData.role === 'admin' ? 'selected' : ''}`}
                  onClick={() => { setInviteData({ ...inviteData, role: 'admin' }); setShowRoleDropdown(false); }}
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.6rem 1rem', cursor: 'pointer', borderLeft: inviteData.role === 'admin' ? '3px solid #6366f1' : '3px solid transparent', background: inviteData.role === 'admin' ? '#f8fafc' : 'transparent' }}
                >
                  <div className="invite-option-content" style={{ textAlign: 'left' }}>
                    <span className="invite-option-title" style={{ fontSize: '0.825rem', fontWeight: 600, color: '#1e293b' }}>Admin</span>
                    <div className="invite-option-desc" style={{ fontSize: '0.725rem', color: '#64748b', marginTop: '2px' }}>Can manage Spaces, People, Billing and other Workspace settings.</div>
                  </div>
                  {inviteData.role === 'admin' && <span className="invite-option-checkmark" style={{ color: '#6366f1', fontSize: '0.85rem', fontWeight: 'bold' }}>✓</span>}
                </div>
                <div className="invite-dropdown-divider" style={{ height: '1px', background: '#f1f5f9', margin: '0.4rem 0' }}></div>
                {/* Add Custom Role */}
                <div className="invite-role-option-custom" style={{ padding: '0.5rem 1rem', textAlign: 'left', color: '#94a3b8', fontSize: '0.8rem', cursor: 'not-allowed', fontStyle: 'italic' }}>
                  <span>+ Add custom role</span>
                </div>"""

block3_replace = """                {/* Admin option */}
                <div
                  className={`invite-role-option ${inviteData.role === 'admin' ? 'selected' : ''}`}
                  onClick={() => { setInviteData({ ...inviteData, role: 'admin' }); setShowRoleDropdown(false); }}
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.6rem 1rem', cursor: 'pointer', borderLeft: inviteData.role === 'admin' ? '3px solid #6366f1' : '3px solid transparent', background: inviteData.role === 'admin' ? '#f8fafc' : 'transparent' }}
                >
                  <div className="invite-option-content" style={{ textAlign: 'left' }}>
                    <span className="invite-option-title" style={{ fontSize: '0.825rem', fontWeight: 600, color: '#1e293b' }}>Admin</span>
                    <div className="invite-option-desc" style={{ fontSize: '0.725rem', color: '#64748b', marginTop: '2px' }}>Can manage Spaces, People, Billing and other Workspace settings.</div>
                  </div>
                  {inviteData.role === 'admin' && <span className="invite-option-checkmark" style={{ color: '#6366f1', fontSize: '0.85rem', fontWeight: 'bold' }}>✓</span>}
                </div>
                {/* Owner option */}
                {selectedOrgMemberRole === 'owner' && (
                  <div
                    className={`invite-role-option ${inviteData.role === 'owner' ? 'selected' : ''}`}
                    onClick={() => { setInviteData({ ...inviteData, role: 'owner' }); setShowRoleDropdown(false); }}
                    style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.6rem 1rem', cursor: 'pointer', borderLeft: inviteData.role === 'owner' ? '3px solid #6366f1' : '3px solid transparent', background: inviteData.role === 'owner' ? '#f8fafc' : 'transparent' }}
                  >
                    <div className="invite-option-content" style={{ textAlign: 'left' }}>
                      <span className="invite-option-title" style={{ fontSize: '0.825rem', fontWeight: 600, color: '#1e293b' }}>Owner</span>
                      <div className="invite-option-desc" style={{ fontSize: '0.725rem', color: '#64748b', marginTop: '2px' }}>Full access to all Workspace settings and billing.</div>
                    </div>
                    {inviteData.role === 'owner' && <span className="invite-option-checkmark" style={{ color: '#6366f1', fontSize: '0.85rem', fontWeight: 'bold' }}>✓</span>}
                  </div>
                )}"""

if block3_search in content:
    content = content.replace(block3_search, block3_replace)
    print("Replaced Block 3")
else:
    print("Could not find Block 3")

with open(app_jsx_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
