import { useState, useEffect, useRef, useMemo } from 'react';
import EmojiPicker from 'emoji-picker-react';
import { useChatSocket } from './useChatSocket';
import api, { getOrganizationMembers } from '../../api';

// Icons
import { MessageSquare, Users, Plus, Send, Smile, Paperclip, MoreVertical, Edit, Trash2, CornerUpLeft, X, Search, CheckSquare, Target } from 'lucide-react';

const parseJwt = (token) => {
  try { return JSON.parse(atob(token.split('.')[1])); } catch { return null; }
};

export default function ChatLayout({ activeOrg, initialRoomId }) {
    const orgSlug = activeOrg?.slug;
    const token = sessionStorage.getItem('access_token');
    const [roomId, setRoomId] = useState(initialRoomId || null);

    const activeRoomIdRef = useRef(roomId);
    useEffect(() => {
        activeRoomIdRef.current = roomId;
    }, [roomId]);
    
    const { 
        messages, setMessages, typingUsers, rooms, setRooms, 
        sendMessage, sendTypingStatus, markAsRead, editMessage, deleteMessage, reactToMessage
    } = useChatSocket(activeOrg?.id, token, activeRoomIdRef);

    const [activeRoomSnapshot, setActiveRoomSnapshot] = useState(null);
    const [newMessage, setNewMessage] = useState('');
    const [files, setFiles] = useState([]);
    const [showEmojiPicker, setShowEmojiPicker] = useState(false);
    const [editingMessage, setEditingMessage] = useState(null);
    const [replyingToMessage, setReplyingToMessage] = useState(null);
    const [hoveredMessageId, setHoveredMessageId] = useState(null);
    const [showProfileModal, setShowProfileModal] = useState(false);
    const [selectedUser, setSelectedUser] = useState(null);
    const [showReactionPicker, setShowReactionPicker] = useState(null); // stores message ID
    const [showSearch, setShowSearch] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const fileInputRef = useRef(null);
    const [loadingRooms, setLoadingRooms] = useState(true);
    const [showNewChat, setShowNewChat] = useState(false);
    const [members, setMembers] = useState([]);
    const [isCreatingGroup, setIsCreatingGroup] = useState(false);
    const [groupName, setGroupName] = useState('');
    const [selectedMembers, setSelectedMembers] = useState([]);

    useEffect(() => {
        if (showNewChat && activeOrg?.id) {
            getOrganizationMembers(activeOrg.id).then(data => {
                // Filter out self
                const me = parseJwt(token)?.user_id;
                setMembers(data.filter(m => m.user_id !== me));
            });
        }
    }, [showNewChat, activeOrg?.id, token]);

    const activeRoom = useMemo(() => {
        if (!roomId) return null;
        if (activeRoomSnapshot?.id === roomId) return activeRoomSnapshot;
        return rooms.find(r => r.id === roomId) || null;
    }, [roomId, activeRoomSnapshot, rooms]);

    const startDirectChat = async (userId) => {
        try {
            const res = await api.post(`org/${orgSlug}/chat/rooms/direct/`, { user_id: userId });
            setRoomId(res.data.id);
            setActiveRoomSnapshot(res.data);
            if (!rooms.find(r => r.id === res.data.id)) setRooms(prev => [res.data, ...prev]);
            setShowNewChat(false);
        } catch(e) { console.error(e); }
    };

    const startGroupChat = async () => {
        if (!groupName.trim() || selectedMembers.length === 0) return;
        try {
            const res = await api.post(`org/${orgSlug}/chat/rooms/group/`, { 
                name: groupName, 
                member_ids: selectedMembers 
            });
            setRoomId(res.data.id);
            setActiveRoomSnapshot(res.data);
            if (!rooms.find(r => r.id === res.data.id)) setRooms(prev => [res.data, ...prev]);
            setShowNewChat(false);
            setIsCreatingGroup(false);
            setGroupName('');
            setSelectedMembers([]);
        } catch(e) { console.error(e); }
    };

    // Fetch initial room list
    useEffect(() => {
        if (!orgSlug) return;
        const fetchRooms = async () => {
            try {
                const res = await api.get(`org/${orgSlug}/chat/rooms/`);
                setRooms(res.data);
                if (initialRoomId) {
                    setRoomId(initialRoomId);
                }
            } catch (err) {
                console.error("Failed to fetch rooms", err);
            } finally {
                setLoadingRooms(false);
            }
        };
        fetchRooms();
    }, [orgSlug, initialRoomId, setRooms]);

    // Fetch messages when a room is selected
    useEffect(() => {
        if (!roomId || !orgSlug) {
            return;
        }

        const room = rooms.find(r => r.id === roomId);
        if (room?.unread_count > 0) {
            setRooms(prevRooms => prevRooms.map(r => r.id === roomId ? { ...r, unread_count: 0 } : r));
        }

        const fetchMessages = async () => {
            try {
                const res = await api.get(`org/${orgSlug}/chat/rooms/${roomId}/messages/`);
                setMessages(res.data); 
                
                if (res.data.length > 0) {
                    markAsRead(roomId, res.data[res.data.length - 1].id);
                }
            } catch (err) {
                console.error("Failed to fetch messages", err);
            }
        };
        fetchMessages();
    }, [roomId, orgSlug, rooms, setMessages, markAsRead, setRooms]);

        const onEmojiClick = (emojiObject) => {
        setNewMessage(prevInput => prevInput + emojiObject.emoji);
        setShowEmojiPicker(false);
    };

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if ((!newMessage.trim() && files.length === 0) || !roomId) return;
        
        if (editingMessage) {
            editMessage(roomId, editingMessage.id, newMessage);
            setEditingMessage(null);
            setNewMessage('');
            sendTypingStatus(roomId, false);
            return;
        }

        if (files.length > 0) {
            const formData = new FormData();
            if (newMessage.trim()) formData.append('content', newMessage);
            if (replyingToMessage) formData.append('reply_to', replyingToMessage.id);
            files.forEach(f => formData.append('files', f));
            try {
                await api.post(`org/${orgSlug}/chat/rooms/${roomId}/messages/`, formData);
                setFiles([]);
                setNewMessage('');
                setReplyingToMessage(null);
                sendTypingStatus(roomId, false);
            } catch (err) {
                console.error('File upload failed', err.response?.data || err);
                alert('File upload failed: ' + JSON.stringify(err.response?.data || err.message));
            }
        } else {
            sendMessage(roomId, newMessage, replyingToMessage?.id);
            setReplyingToMessage(null);
            setNewMessage('');
            sendTypingStatus(roomId, false);
        }
    };

    const handleTyping = (e) => {
        setNewMessage(e.target.value);
        sendTypingStatus(roomId, e.target.value.length > 0);
    };

    return (
        <div style={{ display: 'flex', height: 'calc(100vh - 60px)', backgroundColor: '#f8fafc', margin: '-20px' }}>
            {/* Sidebar */}
            <div style={{ width: '350px', backgroundColor: '#ffffff', borderRight: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column' }}>
                <div style={{ padding: '20px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h2 style={{ margin: 0, fontSize: '1.25rem', color: '#0f172a', fontWeight: '600' }}>Chats</h2>
                    <button onClick={() => setShowNewChat(true)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#3b82f6' }}>
                        <Plus size={20} />
                    </button>
                </div>
                
                <div style={{ padding: '10px 20px' }}>
                    <input 
                        type="text" 
                        placeholder="Search chats..." 
                        style={{ width: '100%', padding: '10px 15px', borderRadius: '8px', border: '1px solid #cbd5e1', outline: 'none' }}
                    />
                </div>

                <div style={{ flex: 1, overflowY: 'auto' }}>
                    {loadingRooms ? (
                        <p style={{ textAlign: 'center', color: '#64748b', marginTop: '20px' }}>Loading chats...</p>
                    ) : rooms.map(room => (
                        <div 
                            key={room.id} 
                            onClick={() => setRoomId(room.id)}
                            style={{ 
                                padding: '15px 20px', display: 'flex', alignItems: 'center', cursor: 'pointer',
                                backgroundColor: roomId === room.id ? '#eff6ff' : 'transparent',
                                borderBottom: '1px solid #f1f5f9'
                            }}
                        >
                            <div style={{ width: '45px', height: '45px', borderRadius: '50%', backgroundColor: room.room_type === 'task' ? '#eef2ff' : room.room_type === 'goal' ? '#fffbeb' : room.room_type === 'group' ? '#e0e7ff' : '#dcfce3', display: 'flex', justifyContent: 'center', alignItems: 'center', marginRight: '15px', flexShrink: 0 }}>
                                {room.room_type === 'task' ? <CheckSquare size={20} color="#4f46e5" /> : 
                                 room.room_type === 'goal' ? <Target size={20} color="#d97706" /> : 
                                 room.room_type === 'group' ? <Users size={20} color="#4f46e5" /> : 
                                 <MessageSquare size={20} color="#16a34a" />}
                            </div>
                            <div style={{ flex: 1, overflow: 'hidden' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                                    <h4 style={{ margin: 0, fontSize: '0.95rem', color: '#1e293b', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                        {room.name}
                                    </h4>
                                    <span style={{ fontSize: '0.75rem', color: '#94a3b8', marginLeft: '8px', flexShrink: 0 }}>
                                        {room.latest_message ? new Date(room.latest_message.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', hour12: false}) : ''}
                                    </span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <p style={{ margin: 0, fontSize: '0.85rem', color: '#64748b', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                        {room.latest_message ? room.latest_message.content : 'No messages yet'}
                                    </p>
                                    {room.room_type !== 'direct' && room.participants && (
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: '#94a3b8', marginLeft: '8px', flexShrink: 0 }}>
                                            <Users size={12} /> {room.participants.length}
                                        </div>
                                    )}
                                </div>
                            </div>
                            {room.unread_count > 0 && (
                                <div style={{ minWidth: '20px', height: '20px', borderRadius: '10px', backgroundColor: '#ef4444', color: 'white', fontSize: '0.75rem', display: 'flex', justifyContent: 'center', alignItems: 'center', marginLeft: '10px', padding: '0 6px' }}>
                                    {room.unread_count}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {/* Active Chat Area */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                {!activeRoom ? (
                    <div style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', flexDirection: 'column', color: '#94a3b8' }}>
                        <MessageSquare size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
                        <h3 style={{ margin: 0 }}>Select a chat to start messaging</h3>
                    </div>
                ) : (
                    <>
                        <div style={{ padding: '20px', backgroundColor: '#ffffff', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div style={{ display: 'flex', alignItems: 'center' }}>
                                <div style={{ width: '40px', height: '40px', borderRadius: '50%', backgroundColor: activeRoom.room_type === 'task' ? '#eef2ff' : activeRoom.room_type === 'goal' ? '#fffbeb' : activeRoom.room_type === 'group' ? '#e0e7ff' : '#dcfce3', display: 'flex', justifyContent: 'center', alignItems: 'center', marginRight: '15px' }}>
                                    {activeRoom.room_type === 'task' ? <CheckSquare size={18} color="#4f46e5" /> : 
                                     activeRoom.room_type === 'goal' ? <Target size={18} color="#d97706" /> : 
                                     activeRoom.room_type === 'group' ? <Users size={18} color="#4f46e5" /> : 
                                     <MessageSquare size={18} color="#16a34a" />}
                                </div>
                                <div 
                                    style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column' }}
                                    onClick={() => {
                                        if (activeRoom.room_type === 'direct') {
                                            const other = activeRoom.participants.find(p => p.user.id !== parseJwt(token)?.user_id);
                                            if (other) { setSelectedUser(other.user); setShowProfileModal(true); }
                                        }
                                    }}
                                >
                                    <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#0f172a' }}>{activeRoom.name}</h3>
                                    {activeRoom.room_type !== 'direct' && activeRoom.participants && (
                                        <span style={{ fontSize: '0.8rem', color: '#64748b' }}>
                                            {activeRoom.participants.length} members
                                        </span>
                                    )}
                                </div>
                            </div>
                            <div style={{ display: 'flex', gap: '15px', color: '#64748b', alignItems: 'center' }}>
                                {showSearch && (
                                    <input 
                                        type="text" 
                                        placeholder="Search messages..." 
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        style={{ padding: '4px 8px', borderRadius: '4px', border: '1px solid #cbd5e1', outline: 'none', fontSize: '0.85rem' }}
                                        autoFocus
                                    />
                                )}
                                <Search size={20} style={{ cursor: 'pointer' }} onClick={() => setShowSearch(!showSearch)} />
                                <MoreVertical size={20} style={{ cursor: 'pointer' }} />
                            </div>
                        </div>

                        <div style={{ flex: 1, padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                            {messages.filter(m => !searchQuery || (m.content && m.content.toLowerCase().includes(searchQuery.toLowerCase()))).map((msg, index) => {
                                const isMe = msg.sender?.id === parseJwt(sessionStorage.getItem('access_token'))?.user_id; 
                                return (
                                    <div 
                                        key={index} 
                                        style={{ alignSelf: isMe ? 'flex-end' : 'flex-start', maxWidth: '60%', position: 'relative', display: 'flex', flexDirection: 'column' }}
                                        onMouseEnter={() => setHoveredMessageId(msg.id)}
                                        onMouseLeave={() => setHoveredMessageId(null)}
                                    >
                                        {!isMe && activeRoom.room_type === 'group' && (
                                            <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '4px', marginLeft: '12px' }}>
                                                {msg.sender?.first_name || msg.sender?.email}
                                            </div>
                                        )}
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexDirection: isMe ? 'row-reverse' : 'row' }}>
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
                                                        {msg.content && <div>{msg.content}</div>}
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
                                                        )}
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
                                                    </>
                                                )}
                                            </div>
                                            
                                            {msg.reactions && msg.reactions.length > 0 && (
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

                                            {/* Hover Actions */}
                                            {hoveredMessageId === msg.id && !msg.is_deleted && (
                                                <div style={{ display: 'flex', gap: '8px', backgroundColor: '#ffffff', padding: '4px 8px', borderRadius: '16px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
                                                    <div style={{ position: 'relative' }}>
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
                                            <span>{new Date(msg.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', hour12: false})}</span>
                                            {msg.is_edited && !msg.is_deleted && <span style={{ fontStyle: 'italic' }}>(edited)</span>}
                                        </div>
                                    </div>
                                );
                            })}
                            
                            {typingUsers[roomId] && Object.values(typingUsers[roomId]).some(t => t) && (
                                <div style={{ alignSelf: 'flex-start', color: '#94a3b8', fontSize: '0.85rem', fontStyle: 'italic', padding: '0 10px' }}>
                                    Someone is typing...
                                </div>
                            )}
                        </div>

                        <div style={{ padding: '20px', backgroundColor: '#ffffff', borderTop: '1px solid #e2e8f0' }}>
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
                            {files.length > 0 && (
                                <div style={{ display: 'flex', gap: '10px', marginBottom: '10px', flexWrap: 'wrap' }}>
                                    {files.map((f, i) => (
                                        <div key={i} style={{ background: '#e2e8f0', padding: '5px 10px', borderRadius: '12px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '5px' }}>
                                            {f.name}
                                            <button type="button" onClick={() => setFiles(files.filter((_, idx) => idx !== i))} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>&times;</button>
                                        </div>
                                    ))}
                                </div>
                            )}
                            <form onSubmit={handleSendMessage} style={{ display: 'flex', alignItems: 'center', backgroundColor: '#f1f5f9', padding: '8px 15px', borderRadius: (replyingToMessage || editingMessage) ? '0 0 24px 24px' : '24px' }}>
                                <input type="file" multiple ref={fileInputRef} style={{ display: 'none' }} onChange={(e) => setFiles(Array.from(e.target.files))} />
                                <div style={{ position: 'relative' }}>
                                    <Smile size={20} color="#64748b" style={{ cursor: 'pointer', marginRight: '15px' }} onClick={() => setShowEmojiPicker(prev => !prev)} />
                                    {showEmojiPicker && (
                                        <div style={{ position: 'absolute', bottom: '40px', left: 0, zIndex: 100 }}>
                                            <EmojiPicker onEmojiClick={onEmojiClick} />
                                        </div>
                                    )}
                                </div>
                                <Paperclip size={20} color="#64748b" style={{ cursor: 'pointer', marginRight: '15px' }} onClick={() => fileInputRef.current.click()} />
                                <input 
                                    type="text" 
                                    value={newMessage}
                                    onChange={handleTyping}
                                    placeholder="Type a message..."
                                    style={{ flex: 1, border: 'none', background: 'transparent', outline: 'none', fontSize: '0.95rem' }}
                                />
                                <button type="submit" style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: newMessage.trim() ? '#3b82f6' : '#94a3b8', padding: '5px' }}>
                                    <Send size={20} />
                                </button>
                            </form>
                        </div>
                    </>
                )}
            </div>

            {/* Profile Modal */}
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

            {/* New Chat Modal */}
            {showNewChat && (
                <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <div style={{ background: '#fff', padding: '20px', borderRadius: '12px', width: '400px', maxHeight: '80vh', overflowY: 'auto' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '15px' }}>
                            <h3 style={{ margin: 0 }}>{isCreatingGroup ? 'New Group Chat' : 'New Chat'}</h3>
                            <button onClick={() => setShowNewChat(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2rem' }}>&times;</button>
                        </div>

                        {!isCreatingGroup && (
                            <button onClick={() => setIsCreatingGroup(true)} style={{ width: '100%', padding: '10px', background: '#eef2ff', color: '#4f46e5', border: 'none', borderRadius: '8px', cursor: 'pointer', marginBottom: '15px', fontWeight: 'bold' }}>
                                + Create New Group
                            </button>
                        )}

                        {isCreatingGroup && (
                            <input 
                                type="text" 
                                placeholder="Group Name" 
                                value={groupName}
                                onChange={e => setGroupName(e.target.value)}
                                style={{ width: '100%', padding: '10px', marginBottom: '15px', borderRadius: '8px', border: '1px solid #ccc' }}
                            />
                        )}

                        <div style={{ marginBottom: '15px' }}>
                            <h4 style={{ margin: '0 0 10px 0', fontSize: '0.9rem', color: '#64748b' }}>Select Members</h4>
                            {members.map(m => (
                                <div key={m.id} style={{ display: 'flex', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid #f1f5f9', cursor: 'pointer' }} onClick={() => {
                                    if (isCreatingGroup) {
                                        setSelectedMembers(prev => prev.includes(m.user_id) ? prev.filter(id => id !== m.user_id) : [...prev, m.user_id]);
                                    } else {
                                        startDirectChat(m.user_id);
                                    }
                                }}>
                                    {isCreatingGroup && (
                                        <input type="checkbox" checked={selectedMembers.includes(m.user_id)} readOnly style={{ marginRight: '10px' }} />
                                    )}
                                    <div style={{ width: '30px', height: '30px', borderRadius: '50%', background: '#e2e8f0', marginRight: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.8rem' }}>
                                        {m.email[0].toUpperCase()}
                                    </div>
                                    <span style={{ fontSize: '0.9rem' }}>{m.email}</span>
                                </div>
                            ))}
                        </div>

                        {isCreatingGroup && (
                            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                                <button onClick={() => setIsCreatingGroup(false)} style={{ padding: '8px 15px', border: 'none', background: '#e2e8f0', borderRadius: '6px', cursor: 'pointer' }}>Back</button>
                                <button onClick={startGroupChat} disabled={!groupName.trim() || selectedMembers.length === 0} style={{ padding: '8px 15px', border: 'none', background: '#3b82f6', color: '#fff', borderRadius: '6px', cursor: 'pointer', opacity: (!groupName.trim() || selectedMembers.length === 0) ? 0.5 : 1 }}>Create Group</button>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
