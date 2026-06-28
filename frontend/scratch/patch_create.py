import re

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace setShowCreateModal(true) with setView('create_workspace')
content = content.replace('setShowCreateModal(true)', "setView('create_workspace')")

# 2. In handleCreateOrganization, when it succeeds, it fetches workspaces. We don't need to change anything there.
# Wait, handleCreateOrganization calls setShowCreateModal(false). Let's remove it.
content = content.replace('setShowCreateModal(false);', '')

# 3. Find the exact modal block and remove it.
modal_start_str = '''        {showCreateModal && (
          <div className="modal-overlay">
            <div className="modal-card">
              <h2 className="form-title" style={{ textAlign: 'left' }}>Create Workspace</h2>'''
# We can use regex to delete the modal block.
modal_regex = re.compile(r'\{showCreateModal && \(\s*<div className="modal-overlay">\s*<div className="modal-card">\s*<h2 className="form-title"[^>]*>Create Workspace</h2>.*?</form>\s*</div>\s*</div>\s*\)\}', re.DOTALL)
content = modal_regex.sub('', content)

# 4. Add the new view
new_view_code = '''
  if (view === 'create_workspace') {
    return (
      <div style={{
        animation: 'slideInRight 0.4s ease-out forwards',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#f8fafc'
      }}>
        <div style={{
          background: 'white',
          padding: '3.5rem',
          borderRadius: '24px',
          boxShadow: '0 20px 40px -10px rgba(0, 0, 0, 0.1)',
          width: '100%',
          maxWidth: '550px'
        }}>
          <h1 className="form-title" style={{ fontSize: '2.5rem', marginBottom: '0.5rem', textAlign: 'left' }}>Create Workspace</h1>
          <p className="form-subtitle" style={{ textAlign: 'left', marginBottom: '2.5rem', fontSize: '1.1rem' }}>Set up a new environment for your team to collaborate seamlessly.</p>
          
          <form onSubmit={handleCreateOrganization}>
            <div className="input-group" style={{ marginBottom: '2rem' }}>
              <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.9rem', marginBottom: '0.5rem' }}>WORKSPACE NAME</label>
              <input 
                className="input-field" 
                placeholder="e.g. Acme Corp" 
                value={newOrgData.name}
                onChange={e => setNewOrgData({...newOrgData, name: e.target.value})}
                required 
                style={{ background: '#f8fafc', border: '1px solid #cbd5e1', padding: '1rem', borderRadius: '12px', fontSize: '1.1rem', transition: 'border 0.2s, box-shadow 0.2s' }}
                onFocus={(e) => { e.target.style.border = '1px solid #6366f1'; e.target.style.boxShadow = '0 0 0 3px rgba(99,102,241,0.1)'; }}
                onBlur={(e) => { e.target.style.border = '1px solid #cbd5e1'; e.target.style.boxShadow = 'none'; }}
              />
            </div>
            <div className="input-group" style={{ marginBottom: '3rem' }}>
              <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.9rem', marginBottom: '0.5rem' }}>DESCRIPTION (OPTIONAL)</label>
              <textarea 
                className="input-field" 
                placeholder="What is this workspace for?"
                value={newOrgData.description}
                onChange={e => setNewOrgData({...newOrgData, description: e.target.value})}
                rows={3} 
                style={{ background: '#f8fafc', border: '1px solid #cbd5e1', padding: '1rem', borderRadius: '12px', fontSize: '1.1rem', resize: 'vertical', transition: 'border 0.2s, box-shadow 0.2s' }}
                onFocus={(e) => { e.target.style.border = '1px solid #6366f1'; e.target.style.boxShadow = '0 0 0 3px rgba(99,102,241,0.1)'; }}
                onBlur={(e) => { e.target.style.border = '1px solid #cbd5e1'; e.target.style.boxShadow = 'none'; }}
              />
            </div>
            <div style={{ display: 'flex', gap: '1.5rem' }}>
              <button 
                type="button" 
                onClick={() => setView(sessionStorage.getItem('selectedOrgId') ? 'dashboard' : 'onboarding')} 
                style={{ flex: 1, padding: '1rem', fontSize: '1.1rem', background: 'transparent', border: '2px solid #e2e8f0', color: '#64748b', borderRadius: '12px', fontWeight: 600, cursor: 'pointer', transition: 'background 0.2s' }}
                onMouseEnter={(e) => e.target.style.background = '#f1f5f9'}
                onMouseLeave={(e) => e.target.style.background = 'transparent'}
              >
                Go Back
              </button>
              <button 
                type="submit" 
                className="btn-primary" 
                style={{ flex: 2, padding: '1rem', fontSize: '1.1rem', borderRadius: '12px', border: 'none', background: 'linear-gradient(135deg, #6366f1, #4f46e5)', boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)', transition: 'transform 0.2s, box-shadow 0.2s' }} 
                disabled={loading}
                onMouseEnter={(e) => { e.target.style.transform = 'translateY(-2px)'; e.target.style.boxShadow = '0 6px 20px rgba(99, 102, 241, 0.5)'; }}
                onMouseLeave={(e) => { e.target.style.transform = 'none'; e.target.style.boxShadow = '0 4px 14px rgba(99, 102, 241, 0.4)'; }}
              >
                {loading ? <Loader2 className="animate-spin" /> : 'Launch Workspace'}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }
'''

if "if (view === 'create_workspace')" not in content:
    # insert it right after the onboarding view block
    content = content.replace('if (view === \'onboarding\') {', new_view_code + "\n  if (view === 'onboarding') {")

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
