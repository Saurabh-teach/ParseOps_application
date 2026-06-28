import re

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

submissions_block = """                        {activeTask.submissions && activeTask.submissions.length > 0 && (
                          <div className="task-detail-meta-group">
                            <h4 className="task-detail-meta-label">Submissions & Proofs</h4>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                              {activeTask.submissions.map(sub => (
                                <div key={sub.id} style={{ background: '#f8fafc', padding: '0.6rem', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                                    <span style={{ fontWeight: 600, fontSize: '0.75rem', color: '#334155' }}>{sub.user_details.name}</span>
                                    <span style={{ fontSize: '0.65rem', color: '#64748b' }}>{new Date(sub.created_at).toLocaleDateString()}</span>
                                  </div>
                                  {sub.comments && <p style={{ fontSize: '0.75rem', color: '#475569', margin: '0 0 0.4rem 0' }}>{sub.comments}</p>}
                                  {sub.url_links && (
                                    <div style={{ marginBottom: '0.4rem' }}>
                                      {sub.url_links.split(/[\\n,]+/).map((link, idx) => {
                                        const url = link.trim();
                                        if (!url) return null;
                                        return <a key={idx} href={url.startsWith('http') ? url : `http://${url}`} target="_blank" rel="noopener noreferrer" style={{ display: 'block', fontSize: '0.7rem', color: '#4f46e5', textDecoration: 'none', wordBreak: 'break-all' }}>🔗 {url}</a>
                                      })}
                                    </div>
                                  )}
                                  {sub.file_url && (
                                    <a href={sub.file_url} target="_blank" rel="noopener noreferrer" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.7rem', color: '#0f172a', background: '#e2e8f0', padding: '0.2rem 0.5rem', borderRadius: '4px', textDecoration: 'none' }}>
                                      📄 Attachment
                                    </a>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}"""

target1 = """                        )}

                        <div className="task-detail-meta-group">
                          <h4 className="task-detail-meta-label">Priority</h4>"""

replacement1 = """                        )}

""" + submissions_block + """

                        <div className="task-detail-meta-group">
                          <h4 className="task-detail-meta-label">Priority</h4>"""

content = content.replace(target1, replacement1)

target2 = """                        )}

                      </div>

                      <div className="task-detail-meta-group">
                        <h4 className="task-detail-meta-label">Priority</h4>"""

replacement2 = """                        )}
                      </div>

""" + submissions_block.replace('                        ', '                      ') + """

                      <div className="task-detail-meta-group">
                        <h4 className="task-detail-meta-label">Priority</h4>"""

content = content.replace(target2, replacement2)

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("App.jsx patched for rendering Submissions & Proofs")
