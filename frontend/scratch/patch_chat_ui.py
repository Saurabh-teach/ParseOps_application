import re

with open('c:/Users/saura/ParseOps/frontend/src/components/Chat/ChatLayout.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Add Check, CheckCheck
icons_import = "import { MessageSquare, Users, Plus, Send, Smile, Paperclip, MoreVertical, Phone, Video, Edit, Trash2, CornerUpLeft, X, Search } from 'lucide-react';"
new_icons_import = "import { MessageSquare, Users, Plus, Send, Smile, Paperclip, MoreVertical, Phone, Video, Edit, Trash2, CornerUpLeft, X, Search, Check, CheckCheck } from 'lucide-react';"
content = content.replace(icons_import, new_icons_import)

# Add state variables
states_block = """    const [showSearch, setShowSearch] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');"""
new_states_block = """    const [showSearch, setShowSearch] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [onlineUsers, setOnlineUsers] = useState({});
    const [roomReadStates, setRoomReadStates] = useState({});"""
content = content.replace(states_block, new_states_block)

# Update socket callbacks
callbacks_block = """        onReaction: (updatedMessage) => {
            setMessages(prev => prev.map(m => m.id === updatedMessage.id ? updatedMessage : m));
        }"""
new_callbacks_block = """        onReaction: (updatedMessage) => {
            setMessages(prev => prev.map(m => m.id === updatedMessage.id ? updatedMessage : m));
        },
        onPresence: (data) => {
            setOnlineUsers(prev => ({
                ...prev,
                [data.user_id]: { isOnline: data.is_online, lastSeen: data.last_seen }
            }));
        },
        onMessageRead: (data) => {
            setRoomReadStates(prev => ({
                ...prev,
                [data.room_id]: {
                    ...prev[data.room_id],
                    [data.user_id]: data.last_read_at
                }
            }));
        }"""
content = content.replace(callbacks_block, new_callbacks_block)

# Setup initial online/read state when setting active room
active_room_block = """                    const { data } = await api.get(`/${orgSlug}/chat/rooms/${roomId}/messages/`);
                    setMessages(data);"""
new_active_room_block = """                    const { data } = await api.get(`/${orgSlug}/chat/rooms/${roomId}/messages/`);
                    setMessages(data);
                    
                    // Initialize read states
                    const initialReadStates = {};
                    roomData.participants.forEach(p => {
                        initialReadStates[p.user.id] = p.last_read_at;
                    });
                    setRoomReadStates(prev => ({ ...prev, [roomId]: initialReadStates }));
                    
                    // Mark read
                    sendMessage('mark_read', { room_id: roomId, message_id: data[data.length - 1]?.id });"""
if "sendMessage('mark_read'" not in content:
    content = content.replace(active_room_block, new_active_room_block)

# Replace "Someone is typing" with dynamic header
header_block = """                                    <div style={{ fontSize: '0.8rem', color: '#10b981' }}>Someone is typing...</div>
                                )}
                            </div>"""
new_header_block = """                                    <div style={{ fontSize: '0.8rem', color: '#10b981' }}>Typing...</div>
                                ) : activeRoom.room_type === 'direct' ? (() => {
                                    const otherUser = activeRoom.participants.find(p => p.user.id !== currentUser.id)?.user;
                                    const presence = onlineUsers[otherUser?.id];
                                    const isOnline = presence ? presence.isOnline : otherUser?.is_online;
                                    const lastSeen = presence ? presence.lastSeen : otherUser?.last_seen;
                                    if (isOnline) return <div style={{ fontSize: '0.8rem', color: '#10b981' }}>Online</div>;
                                    if (lastSeen) return <div style={{ fontSize: '0.8rem', color: '#64748b' }}>Last seen {new Date(lastSeen).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>;
                                    return null;
                                })() : null}
                            </div>"""
if "const presence = onlineUsers" not in content:
    content = content.replace(header_block, new_header_block)

# Read receipt ticks
timestamp_block = """                                                            <span style={{ fontSize: '0.65rem', opacity: 0.7, marginTop: '5px', display: 'block', textAlign: 'right' }}>
                                                                {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                            </span>"""
new_timestamp_block = """                                                            <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '4px', marginTop: '5px' }}>
                                                                <span style={{ fontSize: '0.65rem', opacity: 0.7 }}>
                                                                    {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                                </span>
                                                                {isMe && (() => {
                                                                    const roomReads = roomReadStates[activeRoom.id] || {};
                                                                    const isReadByAnyone = Object.entries(roomReads).some(([uid, time]) => uid !== currentUser.id && time && new Date(time) >= new Date(msg.created_at));
                                                                    return isReadByAnyone ? <CheckCheck size={14} color="#34b7f1" /> : <Check size={14} color="rgba(255,255,255,0.7)" />;
                                                                })()}
                                                            </div>"""
if "CheckCheck size={14}" not in content:
    content = content.replace(timestamp_block, new_timestamp_block)


with open('c:/Users/saura/ParseOps/frontend/src/components/Chat/ChatLayout.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("ChatLayout.jsx patched for presence and read receipts")
