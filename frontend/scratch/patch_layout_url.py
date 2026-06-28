import re

with open('c:/Users/saura/ParseOps/frontend/src/components/Chat/ChatLayout.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

msg_bubble = """                                                        {msg.content && <div>{msg.content}</div>}"""
new_msg_bubble = """                                                        {msg.content && <div>{msg.content}</div>}
                                                        {msg.url_preview && (
                                                            <a href={msg.url_preview.url} target="_blank" rel="noopener noreferrer" style={{ display: 'block', marginTop: '8px', textDecoration: 'none', color: 'inherit' }}>
                                                                <div style={{ border: `1px solid ${isMe ? 'rgba(255,255,255,0.3)' : '#e2e8f0'}`, borderRadius: '8px', overflow: 'hidden', backgroundColor: isMe ? 'rgba(0,0,0,0.1)' : '#f8fafc' }}>
                                                                    {msg.url_preview.image && <img src={msg.url_preview.image} alt="Preview" style={{ width: '100%', maxHeight: '150px', objectFit: 'cover', display: 'block' }} />}
                                                                    <div style={{ padding: '8px' }}>
                                                                        <strong style={{ fontSize: '0.85rem', display: 'block', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{msg.url_preview.title}</strong>
                                                                        {msg.url_preview.description && <p style={{ margin: '4px 0 0 0', fontSize: '0.75rem', opacity: 0.8, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{msg.url_preview.description}</p>}
                                                                        <span style={{ fontSize: '0.65rem', opacity: 0.6, display: 'block', marginTop: '4px' }}>{new URL(msg.url_preview.url).hostname}</span>
                                                                    </div>
                                                                </div>
                                                            </a>
                                                        )}"""

if "msg.url_preview &&" not in content:
    content = content.replace(msg_bubble, new_msg_bubble)
    with open('c:/Users/saura/ParseOps/frontend/src/components/Chat/ChatLayout.jsx', 'w', encoding='utf-8') as f:
        f.write(content)

print("ChatLayout.jsx patched for url preview")
