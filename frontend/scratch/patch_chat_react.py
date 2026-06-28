import re

with open('c:/Users/saura/ParseOps/frontend/src/components/Chat/ChatLayout.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update useChatSocket import
use_chat_socket_line = """    const { 
        messages, setMessages, typingUsers, rooms, setRooms, 
        sendMessage, sendTypingStatus, markAsRead, editMessage, deleteMessage
    } = useChatSocket(activeOrg?.id, token);"""
new_use_chat_socket_line = """    const { 
        messages, setMessages, typingUsers, rooms, setRooms, 
        sendMessage, sendTypingStatus, markAsRead, editMessage, deleteMessage, reactToMessage
    } = useChatSocket(activeOrg?.id, token);"""
content = content.replace(use_chat_socket_line, new_use_chat_socket_line)

# 2. Add Profile Modal states
states_block = """    const [hoveredMessageId, setHoveredMessageId] = useState(null);"""
new_states_block = """    const [hoveredMessageId, setHoveredMessageId] = useState(null);
    const [showProfileModal, setShowProfileModal] = useState(false);
    const [selectedUser, setSelectedUser] = useState(null);
    const [showReactionPicker, setShowReactionPicker] = useState(null); // stores message ID"""
content = content.replace(states_block, new_states_block)

# 3. Add onClick to chat header to open profile
header_block = """                                <div>
                                    <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#0f172a' }}>{activeRoom.name}</h3>
                                </div>"""
new_header_block = """                                <div 
                                    style={{ cursor: 'pointer' }}
                                    onClick={() => {
                                        if (activeRoom.room_type === 'direct') {
                                            const other = activeRoom.participants.find(p => p.user.id !== parseJwt(token)?.user_id);
                                            if (other) { setSelectedUser(other.user); setShowProfileModal(true); }
                                        }
                                    }}
                                >
                                    <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#0f172a' }}>{activeRoom.name}</h3>
                                </div>"""
content = content.replace(header_block, new_header_block)

# 4. Render reactions below message
msg_end_block = """                                            {/* Hover Actions */}"""
new_msg_end_block = """                                            {msg.reactions && msg.reactions.length > 0 && (
                                                <div style={{ position: 'absolute', bottom: '-12px', [isMe ? 'right' : 'left']: '15px', display: 'flex', gap: '2px', background: '#fff', borderRadius: '12px', padding: '2px 4px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', border: '1px solid #f1f5f9' }}>
                                                    {Object.entries(
                                                        msg.reactions.reduce((acc, r) => { acc[r.emoji] = (acc[r.emoji] || 0) + 1; return acc; }, {})
                                                    ).map(([emoji, count]) => (
                                                        <span key={emoji} style={{ fontSize: '0.75rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '2px' }} onClick={() => reactToMessage(roomId, msg.id, emoji)}>
                                                            {emoji} {count > 1 && <span style={{ fontSize: '0.65rem', color: '#64748b' }}>{count}</span>}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}

                                            {/* Hover Actions */}"""
content = content.replace(msg_end_block, new_msg_end_block)


# 5. Add react button to hover actions
hover_actions = """                                                    <button onClick={() => { setReplyingToMessage(msg); setEditingMessage(null); }} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '2px', color: '#64748b' }} title="Reply">
                                                        <CornerUpLeft size={14} />
                                                    </button>"""
new_hover_actions = """                                                    <div style={{ position: 'relative' }}>
                                                        <button onClick={() => setShowReactionPicker(showReactionPicker === msg.id ? null : msg.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '2px', color: '#64748b' }} title="React">
                                                            <Smile size={14} />
                                                        </button>
                                                        {showReactionPicker === msg.id && (
                                                            <div style={{ position: 'absolute', bottom: '100%', left: '50%', transform: 'translateX(-50%)', marginBottom: '5px', backgroundColor: '#fff', padding: '5px 10px', borderRadius: '20px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)', display: 'flex', gap: '8px', zIndex: 10 }}>
                                                                {['👍', '❤️', '😂', '😮', '😢'].map(emoji => (
                                                                    <span key={emoji} style={{ cursor: 'pointer', fontSize: '1.2rem', transition: 'transform 0.1s' }} onClick={() => { reactToMessage(roomId, msg.id, emoji); setShowReactionPicker(null); }} onMouseEnter={(e) => e.target.style.transform = 'scale(1.2)'} onMouseLeave={(e) => e.target.style.transform = 'scale(1)'}>
                                                                        {emoji}
                                                                    </span>
                                                                ))}
                                                            </div>
                                                        )}
                                                    </div>
                                                    <button onClick={() => { setReplyingToMessage(msg); setEditingMessage(null); }} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '2px', color: '#64748b' }} title="Reply">
                                                        <CornerUpLeft size={14} />
                                                    </button>"""
content = content.replace(hover_actions, new_hover_actions)

# 6. Add Profile Modal at the end
end_block = """            {/* New Chat Modal */}"""
new_end_block = """            {/* Profile Modal */}
            {showProfileModal && selectedUser && (
                <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <div style={{ background: '#fff', padding: '30px', borderRadius: '16px', width: '350px', textAlign: 'center', boxShadow: '0 10px 25px rgba(0,0,0,0.1)' }}>
                        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                            <button onClick={() => setShowProfileModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}><X size={20} /></button>
                        </div>
                        <div style={{ width: '80px', height: '80px', borderRadius: '50%', backgroundColor: '#e0e7ff', display: 'flex', justifyContent: 'center', alignItems: 'center', margin: '0 auto 15px', fontSize: '2rem', color: '#4f46e5', fontWeight: 'bold' }}>
                            {selectedUser.first_name ? selectedUser.first_name[0].toUpperCase() : selectedUser.email[0].toUpperCase()}
                        </div>
                        <h2 style={{ margin: '0 0 5px 0', fontSize: '1.4rem', color: '#0f172a' }}>
                            {selectedUser.first_name ? `${selectedUser.first_name} ${selectedUser.last_name}` : 'User'}
                        </h2>
                        <p style={{ margin: '0 0 20px 0', color: '#64748b', fontSize: '0.95rem' }}>{selectedUser.email}</p>
                        
                        <div style={{ backgroundColor: '#f8fafc', padding: '15px', borderRadius: '12px', textAlign: 'left' }}>
                            <h4 style={{ margin: '0 0 8px 0', fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase' }}>About</h4>
                            <p style={{ margin: 0, fontSize: '0.9rem', color: '#334155' }}>
                                Available on ParseOps. Building amazing things together!
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* New Chat Modal */}"""
content = content.replace(end_block, new_end_block)


with open('c:/Users/saura/ParseOps/frontend/src/components/Chat/ChatLayout.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("ChatLayout.jsx patched for React/Profile")
