with open('c:/Users/saura/ParseOps/frontend/src/components/Chat/ChatLayout.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

parseJwt_code = """const parseJwt = (token) => {
  try { return JSON.parse(atob(token.split('.')[1])); } catch (e) { return null; }
};

export default function ChatLayout({ activeOrg }) {"""

if "const parseJwt =" not in content:
    content = content.replace("export default function ChatLayout({ activeOrg }) {", parseJwt_code)

old_me = "const me = sessionStorage.getItem('user_id');"
new_me = "const me = parseJwt(token)?.user_id;"
content = content.replace(old_me, new_me)

old_isMe = "const isMe = msg.sender?.id === sessionStorage.getItem('user_id');"
new_isMe = "const isMe = msg.sender?.id === parseJwt(sessionStorage.getItem('access_token'))?.user_id;"
content = content.replace(old_isMe, new_isMe)

# File upload logic
if "const [files, setFiles] = useState([]);" not in content:
    state_block = "const [newMessage, setNewMessage] = useState('');"
    new_state_block = "const [newMessage, setNewMessage] = useState('');\n    const [files, setFiles] = useState([]);\n    const fileInputRef = React.useRef(null);"
    content = content.replace(state_block, new_state_block)

old_submit = """    const handleSendMessage = (e) => {
        e.preventDefault();
        if (!newMessage.trim() || !roomId) return;
        sendMessage(roomId, newMessage);
        setNewMessage('');
        sendTypingStatus(roomId, false);
    };"""

new_submit = """    const handleSendMessage = async (e) => {
        e.preventDefault();
        if ((!newMessage.trim() && files.length === 0) || !roomId) return;
        
        if (files.length > 0) {
            const formData = new FormData();
            if (newMessage.trim()) formData.append('content', newMessage);
            files.forEach(f => formData.append('files', f));
            try {
                await api.post(`org/${orgSlug}/chat/rooms/${roomId}/messages/`, formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });
                setFiles([]);
                setNewMessage('');
                sendTypingStatus(roomId, false);
            } catch (err) {
                console.error('File upload failed', err);
            }
        } else {
            sendMessage(roomId, newMessage);
            setNewMessage('');
            sendTypingStatus(roomId, false);
        }
    };"""

content = content.replace(old_submit, new_submit)

# Render attachments
old_render_msg = """                                        <div style={{ 
                                            padding: '10px 15px', 
                                            borderRadius: isMe ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                                            backgroundColor: isMe ? '#3b82f6' : '#ffffff',
                                            color: isMe ? '#ffffff' : '#0f172a',
                                            boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                                            fontSize: '0.95rem',
                                            lineHeight: '1.4'
                                        }}>
                                            {msg.content}
                                        </div>"""

new_render_msg = """                                        <div style={{ 
                                            padding: '10px 15px', 
                                            borderRadius: isMe ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                                            backgroundColor: isMe ? '#3b82f6' : '#ffffff',
                                            color: isMe ? '#ffffff' : '#0f172a',
                                            boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                                            fontSize: '0.95rem',
                                            lineHeight: '1.4'
                                        }}>
                                            {msg.content && <div>{msg.content}</div>}
                                            {msg.attachments && msg.attachments.length > 0 && (
                                                <div style={{ marginTop: msg.content ? '8px' : '0', display: 'flex', flexDirection: 'column', gap: '5px' }}>
                                                    {msg.attachments.map(att => (
                                                        <a 
                                                            key={att.id} 
                                                            href={`http://localhost:8000${att.file}`} 
                                                            target="_blank" 
                                                            rel="noopener noreferrer"
                                                            style={{ 
                                                                color: isMe ? '#eff6ff' : '#3b82f6', 
                                                                textDecoration: 'underline',
                                                                display: 'flex', alignItems: 'center', gap: '5px'
                                                            }}
                                                        >
                                                            <Paperclip size={14} />
                                                            {att.file_name}
                                                        </a>
                                                    ))}
                                                </div>
                                            )}
                                        </div>"""

content = content.replace(old_render_msg, new_render_msg)

# File input UI
old_form = """                            <form onSubmit={handleSendMessage} style={{ display: 'flex', alignItems: 'center', backgroundColor: '#f1f5f9', padding: '8px 15px', borderRadius: '24px' }}>
                                <Smile size={20} color="#64748b" style={{ cursor: 'pointer', marginRight: '15px' }} />
                                <Paperclip size={20} color="#64748b" style={{ cursor: 'pointer', marginRight: '15px' }} />"""

new_form = """                            {files.length > 0 && (
                                <div style={{ display: 'flex', gap: '10px', marginBottom: '10px', flexWrap: 'wrap' }}>
                                    {files.map((f, i) => (
                                        <div key={i} style={{ background: '#e2e8f0', padding: '5px 10px', borderRadius: '12px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '5px' }}>
                                            {f.name}
                                            <button type="button" onClick={() => setFiles(files.filter((_, idx) => idx !== i))} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>&times;</button>
                                        </div>
                                    ))}
                                </div>
                            )}
                            <form onSubmit={handleSendMessage} style={{ display: 'flex', alignItems: 'center', backgroundColor: '#f1f5f9', padding: '8px 15px', borderRadius: '24px' }}>
                                <input type="file" multiple ref={fileInputRef} style={{ display: 'none' }} onChange={(e) => setFiles(Array.from(e.target.files))} />
                                <Smile size={20} color="#64748b" style={{ cursor: 'pointer', marginRight: '15px' }} />
                                <Paperclip size={20} color="#64748b" style={{ cursor: 'pointer', marginRight: '15px' }} onClick={() => fileInputRef.current.click()} />"""

content = content.replace(old_form, new_form)

with open('c:/Users/saura/ParseOps/frontend/src/components/Chat/ChatLayout.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched ChatLayout.jsx with files and parseJwt")
