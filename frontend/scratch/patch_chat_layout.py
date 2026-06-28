import re

with open('c:/Users/saura/ParseOps/frontend/src/components/Chat/ChatLayout.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Icons import
icons_line = "import { MessageSquare, Users, Plus, Send, Smile, Paperclip, MoreVertical, Phone, Video } from 'lucide-react';"
new_icons_line = "import { MessageSquare, Users, Plus, Send, Smile, Paperclip, MoreVertical, Phone, Video, Edit, Trash2, CornerUpLeft, X } from 'lucide-react';"
content = content.replace(icons_line, new_icons_line)

# 2. Update useChatSocket import
use_chat_socket_line = """    const { 
        messages, setMessages, typingUsers, rooms, setRooms, 
        sendMessage, sendTypingStatus, markAsRead 
    } = useChatSocket(activeOrg?.id, token);"""
new_use_chat_socket_line = """    const { 
        messages, setMessages, typingUsers, rooms, setRooms, 
        sendMessage, sendTypingStatus, markAsRead, editMessage, deleteMessage
    } = useChatSocket(activeOrg?.id, token);"""
content = content.replace(use_chat_socket_line, new_use_chat_socket_line)

# 3. Add states
states_block = """    const [newMessage, setNewMessage] = useState('');
    const [files, setFiles] = useState([]);
    const [showEmojiPicker, setShowEmojiPicker] = useState(false);"""
new_states_block = """    const [newMessage, setNewMessage] = useState('');
    const [files, setFiles] = useState([]);
    const [showEmojiPicker, setShowEmojiPicker] = useState(false);
    const [editingMessage, setEditingMessage] = useState(null);
    const [replyingToMessage, setReplyingToMessage] = useState(null);
    const [hoveredMessageId, setHoveredMessageId] = useState(null);"""
content = content.replace(states_block, new_states_block)

# 4. Update handleSendMessage
send_func = """    const handleSendMessage = async (e) => {
        e.preventDefault();
        if ((!newMessage.trim() && files.length === 0) || !roomId) return;
        
        if (files.length > 0) {"""
new_send_func = """    const handleSendMessage = async (e) => {
        e.preventDefault();
        if ((!newMessage.trim() && files.length === 0) || !roomId) return;
        
        if (editingMessage) {
            editMessage(roomId, editingMessage.id, newMessage);
            setEditingMessage(null);
            setNewMessage('');
            sendTypingStatus(roomId, false);
            return;
        }

        if (files.length > 0) {"""
content = content.replace(send_func, new_send_func)

send_else = """        } else {
            sendMessage(roomId, newMessage);
            setNewMessage('');
            sendTypingStatus(roomId, false);
        }"""
new_send_else = """        } else {
            sendMessage(roomId, newMessage, replyingToMessage?.id);
            setReplyingToMessage(null);
            setNewMessage('');
            sendTypingStatus(roomId, false);
        }"""
content = content.replace(send_else, new_send_else)

# 5. Message rendering loop
msg_render = """                                return (
                                    <div key={index} style={{ alignSelf: isMe ? 'flex-end' : 'flex-start', maxWidth: '60%' }}>
                                        {!isMe && activeRoom.room_type === 'group' && ("""
new_msg_render = """                                return (
                                    <div 
                                        key={index} 
                                        style={{ alignSelf: isMe ? 'flex-end' : 'flex-start', maxWidth: '60%', position: 'relative', display: 'flex', flexDirection: 'column' }}
                                        onMouseEnter={() => setHoveredMessageId(msg.id)}
                                        onMouseLeave={() => setHoveredMessageId(null)}
                                    >
                                        {!isMe && activeRoom.room_type === 'group' && ("""
content = content.replace(msg_render, new_msg_render)

# Add Reply/Edit/Delete actions and reply_to_preview
msg_bubble = """                                        <div style={{ 
                                            padding: '10px 15px', 
                                            borderRadius: isMe ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                                            backgroundColor: isMe ? '#3b82f6' : '#ffffff',
                                            color: isMe ? '#ffffff' : '#0f172a',
                                            boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                                            fontSize: '0.95rem',
                                            lineHeight: '1.4'
                                        }}>
                                            {msg.content && <div>{msg.content}</div>}"""
new_msg_bubble = """                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexDirection: isMe ? 'row-reverse' : 'row' }}>
                                            <div style={{ 
                                                padding: '10px 15px', 
                                                borderRadius: isMe ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                                                backgroundColor: isMe ? '#3b82f6' : '#ffffff',
                                                color: isMe ? '#ffffff' : '#0f172a',
                                                boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                                                fontSize: '0.95rem',
                                                lineHeight: '1.4',
                                                position: 'relative'
                                            }}>
                                                {msg.reply_to_preview && (
                                                    <div style={{ padding: '6px 10px', backgroundColor: isMe ? 'rgba(255,255,255,0.2)' : '#f1f5f9', borderRadius: '8px', marginBottom: '8px', fontSize: '0.85rem', borderLeft: `3px solid ${isMe ? '#ffffff' : '#3b82f6'}` }}>
                                                        <strong style={{ display: 'block', fontSize: '0.8rem', opacity: 0.8 }}>{msg.reply_to_preview.sender_name}</strong>
                                                        <span style={{ opacity: 0.9 }}>{msg.reply_to_preview.content || 'Attachment'}</span>
                                                    </div>
                                                )}
                                                {msg.is_deleted ? (
                                                    <div style={{ fontStyle: 'italic', opacity: 0.7 }}>This message was deleted</div>
                                                ) : (
                                                    <>
                                                        {msg.content && <div>{msg.content}</div>}"""
content = content.replace(msg_bubble, new_msg_bubble)

msg_bubble_end = """                                            {msg.attachments && msg.attachments.length > 0 && (
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
                                        </div>
                                        <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginTop: '4px', textAlign: isMe ? 'right' : 'left', margin: isMe ? '0 12px 0 0' : '0 0 0 12px' }}>
                                            {new Date(msg.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                                        </div>"""

new_msg_bubble_end = """                                            {msg.attachments && msg.attachments.length > 0 && (
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
                                                    </>
                                                )}
                                            </div>
                                            
                                            {/* Hover Actions */}
                                            {hoveredMessageId === msg.id && !msg.is_deleted && (
                                                <div style={{ display: 'flex', gap: '8px', backgroundColor: '#ffffff', padding: '4px 8px', borderRadius: '16px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
                                                    <button onClick={() => { setReplyingToMessage(msg); setEditingMessage(null); }} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '2px', color: '#64748b' }} title="Reply">
                                                        <CornerUpLeft size={14} />
                                                    </button>
                                                    {isMe && (
                                                        <>
                                                            <button onClick={() => { setEditingMessage(msg); setNewMessage(msg.content); setReplyingToMessage(null); }} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '2px', color: '#64748b' }} title="Edit">
                                                                <Edit size={14} />
                                                            </button>
                                                            <button onClick={() => deleteMessage(roomId, msg.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '2px', color: '#ef4444' }} title="Delete">
                                                                <Trash2 size={14} />
                                                            </button>
                                                        </>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                        <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginTop: '4px', textAlign: isMe ? 'right' : 'left', margin: isMe ? '0 12px 0 0' : '0 0 0 12px', display: 'flex', justifyContent: isMe ? 'flex-end' : 'flex-start', gap: '5px' }}>
                                            <span>{new Date(msg.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                                            {msg.is_edited && !msg.is_deleted && <span style={{ fontStyle: 'italic' }}>(edited)</span>}
                                        </div>"""
content = content.replace(msg_bubble_end, new_msg_bubble_end)

# 6. Add Replying/Editing banner above input
input_form = """                        <div style={{ padding: '20px', backgroundColor: '#ffffff', borderTop: '1px solid #e2e8f0' }}>
                            {files.length > 0 && ("""
new_input_form = """                        <div style={{ padding: '20px', backgroundColor: '#ffffff', borderTop: '1px solid #e2e8f0' }}>
                            {(replyingToMessage || editingMessage) && (
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#f1f5f9', padding: '10px 15px', borderRadius: '12px 12px 0 0', borderBottom: '2px solid #3b82f6', marginBottom: '2px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', overflow: 'hidden' }}>
                                        {replyingToMessage ? <CornerUpLeft size={16} color="#3b82f6" /> : <Edit size={16} color="#3b82f6" />}
                                        <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                            <strong style={{ fontSize: '0.85rem', color: '#3b82f6', display: 'block' }}>
                                                {replyingToMessage ? `Replying to ${replyingToMessage.sender?.first_name || replyingToMessage.sender?.email}` : 'Editing Message'}
                                            </strong>
                                            <span style={{ fontSize: '0.85rem', color: '#64748b' }}>
                                                {replyingToMessage ? replyingToMessage.content : editingMessage?.content}
                                            </span>
                                        </div>
                                    </div>
                                    <button onClick={() => { setReplyingToMessage(null); setEditingMessage(null); if(editingMessage) setNewMessage(''); }} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}>
                                        <X size={16} />
                                    </button>
                                </div>
                            )}
                            {files.length > 0 && ("""
content = content.replace(input_form, new_input_form)

# Add conditional border radius to form if banner is active
form_line = """<form onSubmit={handleSendMessage} style={{ display: 'flex', alignItems: 'center', backgroundColor: '#f1f5f9', padding: '8px 15px', borderRadius: '24px' }}>"""
new_form_line = """<form onSubmit={handleSendMessage} style={{ display: 'flex', alignItems: 'center', backgroundColor: '#f1f5f9', padding: '8px 15px', borderRadius: (replyingToMessage || editingMessage) ? '0 0 24px 24px' : '24px' }}>"""
content = content.replace(form_line, new_form_line)


with open('c:/Users/saura/ParseOps/frontend/src/components/Chat/ChatLayout.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("ChatLayout.jsx patched")
