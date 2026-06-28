import re

file_path = 'c:/Users/saura/ParseOps/frontend/src/App.jsx'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the notifications block from its current location
start_match = re.search(r"\s*\{activeTab === 'notifications' && \(\s*<div style=\{\{ maxWidth: 860", content)
end_match = re.search(r"\s*\{activeTab === 'history' && \(\(\) => \{", content)

if start_match and end_match:
    block = content[start_match.start():end_match.start()]
    content = content[:start_match.start()] + content[end_match.start():]
    
    # modify block to be conditionally rendered on historySubTab
    block = block.replace("activeTab === 'notifications'", "historySubTab === 'notifications'")
    
    # Find the requests-container and the ternary logic
    target_container = '''                  <div className="requests-container">
                    {historySubTab === 'logs' ? ('''
    replacement_container = f'''                  <div className="requests-container">
{block.rstrip()}
                    {{historySubTab === 'logs' && ('''
                    
    content = content.replace(target_container, replacement_container)
    
    target_recovery = '''                        </div>
                      )
                    ) : (
                      /* Recovery / Trash Section */'''
    replacement_recovery = '''                        </div>
                      )
                    )}
                    {historySubTab === 'recovery' && (
                      /* Recovery / Trash Section */'''
    content = content.replace(target_recovery, replacement_recovery)
    
    # Add the pill
    target_pill = '''                    <button 
                      onClick={() => setHistorySubTab('recovery')}'''
    replacement_pill = '''                    <button 
                      onClick={() => setHistorySubTab('notifications')}
                      style={{
                        padding: '0.5rem 1.25rem',
                        borderRadius: '20px',
                        border: 'none',
                        fontSize: '0.85rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        background: historySubTab === 'notifications' ? '#3b82f6' : '#f1f5f9',
                        color: historySubTab === 'notifications' ? 'white' : '#64748b',
                        boxShadow: historySubTab === 'notifications' ? '0 4px 6px -1px rgba(59, 130, 246, 0.2)' : 'none'
                      }}
                    >
                      Notifications ({notifications.filter(n => !n.is_read).length})
                    </button>
                    <button 
                      onClick={() => setHistorySubTab('recovery')}'''
    content = content.replace(target_pill, replacement_pill)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
        print("Successfully updated App.jsx")
else:
    print("Could not find the necessary blocks.")
