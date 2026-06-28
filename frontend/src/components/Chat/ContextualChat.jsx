import React, { useState, useEffect, useRef } from 'react';
import { Send, FileText, Image as ImageIcon, Smile, MoreVertical, Edit2, Trash2, X, Paperclip, File as FileIcon, Download } from 'lucide-react';
import EmojiPicker from 'emoji-picker-react';
import { useChatSocket } from './useChatSocket';
import api, { baseURL } from '../../api';

const ContextualChat = ({ roomId, orgSlug, orgId, currentUser, title = "Discussion", memberCount = 0 }) => {
    const { messages, setMessages, sendMessage, editMessage, deleteMessage, markAsRead, joinRoom, isConnected } = useChatSocket(orgId, sessionStorage.getItem('access_token'));
    const [newMessage, setNewMessage] = useState('');
    const [isLoading, setIsLoading] = useState(true);
    const [editingMessageId, setEditingMessageId] = useState(null);
    const messagesEndRef = useRef(null);
    const [activeOptions, setActiveOptions] = useState(null);
    
    // New states for chat input features
    const [showEmojiPicker, setShowEmojiPicker] = useState(false);
    const [attachedFiles, setAttachedFiles] = useState([]);
    const [isUploading, setIsUploading] = useState(false);
    const fileInputRef = useRef(null);
    const emojiPickerRef = useRef(null);

    // Fetch initial messages
    useEffect(() => {
        if (!roomId || !orgSlug) return;
        
        const fetchMessages = async () => {
            try {
                setIsLoading(true);
                const res = await api.get(`/org/${orgSlug}/chat/rooms/${roomId}/messages/`);
                setMessages(res.data.results || res.data);
                setIsLoading(false);
            } catch (err) {
                console.error("Failed to fetch messages", err);
                setIsLoading(false);
            }
        };
        fetchMessages();
    }, [roomId, orgSlug, setMessages]);

    useEffect(() => {
        if (isConnected && roomId) {
            joinRoom(roomId);
        }
    }, [isConnected, roomId, joinRoom]);

    // Scroll to bottom
    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
        
        // Mark latest message as read
        if (Array.isArray(messages) && messages.length > 0) {
            const lastMessage = messages[messages.length - 1];
            if (lastMessage && lastMessage.id) {
                markAsRead(roomId, lastMessage.id);
            }
        }
    }, [messages, roomId, markAsRead]);

    // Close emoji picker when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (emojiPickerRef.current && !emojiPickerRef.current.contains(event.target)) {
                setShowEmojiPicker(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleSend = async (e) => {
        e.preventDefault();
        if ((!newMessage.trim() && attachedFiles.length === 0) || isUploading) return;
        
        if (editingMessageId) {
            editMessage(roomId, editingMessageId, newMessage);
            setEditingMessageId(null);
            setNewMessage('');
        } else {
            if (attachedFiles.length > 0) {
                // Send via API for files
                try {
                    setIsUploading(true);
                    const formData = new FormData();
                    if (newMessage.trim()) formData.append('content', newMessage);
                    attachedFiles.forEach(file => formData.append('files', file));
                    
                    await api.post(`/org/${orgSlug}/chat/rooms/${roomId}/messages/`, formData);
                    
                    setNewMessage('');
                    setAttachedFiles([]);
                    setShowEmojiPicker(false);
                } catch (err) {
                    console.error("Failed to upload message files", err);
                    alert("Failed to send files. Please try again.");
                } finally {
                    setIsUploading(false);
                }
            } else {
                // Text only
                sendMessage(roomId, newMessage);
                setNewMessage('');
                setShowEmojiPicker(false);
            }
        }
    };

    const handleFileSelect = (e) => {
        if (e.target.files && e.target.files.length > 0) {
            const filesArray = Array.from(e.target.files);
            setAttachedFiles(prev => [...prev, ...filesArray]);
        }
        e.target.value = '';
    };

    const removeFile = (indexToRemove) => {
        setAttachedFiles(prev => prev.filter((_, index) => index !== indexToRemove));
    };

    const onEmojiClick = (emojiObject) => {
        setNewMessage(prev => prev + emojiObject.emoji);
    };

    const getFileIcon = (mimeType) => {
        if (!mimeType) return <FileIcon size={14} />;
        if (mimeType.startsWith('image/')) return <ImageIcon size={14} />;
        if (mimeType.includes('pdf')) return <FileText size={14} />;
        return <FileIcon size={14} />;
    };

    const renderAttachments = (attachments, isMine) => {
        if (!attachments || attachments.length === 0) return null;
        
        return (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginTop: '0.5rem' }}>
                {attachments.map(att => {
                    const fileUrl = att.file.startsWith('http') 
                        ? att.file 
                        : att.file.startsWith('/media/')
                            ? `${baseURL}${att.file}`
                            : `${baseURL}/media/${att.file}`;
                    return (
                        <a 
                            key={att.id} 
                            href={fileUrl} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            style={{ 
                                display: 'flex', alignItems: 'center', gap: '0.5rem', 
                                padding: '0.4rem 0.6rem', 
                                background: isMine ? 'rgba(255,255,255,0.2)' : '#f1f5f9', 
                                borderRadius: '0.25rem',
                                color: isMine ? 'white' : '#0f172a',
                                textDecoration: 'none',
                                fontSize: '0.8rem'
                            }}
                        >
                            {getFileIcon(att.file_type)}
                            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '200px' }}>
                                {att.file_name}
                            </span>
                            <Download size={14} style={{ marginLeft: 'auto', opacity: 0.7 }} />
                        </a>
                    );
                })}
            </div>
        );
    };

    const handleDelete = (msgId) => {
        if (window.confirm("Are you sure you want to delete this message?")) {
            deleteMessage(roomId, msgId);
            setActiveOptions(null);
        }
    };

    const handleEditStart = (msg) => {
        setEditingMessageId(msg.id);
        setNewMessage(msg.content);
        setActiveOptions(null);
    };

    if (!roomId) {
        return (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>
                Chat is not available for this item yet.
            </div>
        );
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#f8fafc', borderRadius: '0.5rem', overflow: 'hidden', border: '1px solid #e2e8f0' }}>
            {/* Header */}
            <div style={{ padding: '0.75rem 1rem', background: 'white', borderBottom: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                    <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 600, color: '#0f172a' }}>{title}</h3>
                    <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.1rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        <span style={{ display: 'inline-block', width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#22c55e' }}></span>
                        {memberCount} {memberCount === 1 ? 'member' : 'members'}
                    </div>
                </div>
            </div>
            
            {/* Messages Area */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {isLoading ? (
                    <div style={{ textAlign: 'center', color: '#94a3b8', marginTop: '2rem' }}>Loading messages...</div>
                ) : (!Array.isArray(messages) || messages.length === 0) ? (
                    <div style={{ textAlign: 'center', color: '#94a3b8', marginTop: '2rem', fontSize: '0.9rem' }}>
                        No messages yet. Start the conversation!
                    </div>
                ) : (
                    (Array.isArray(messages) ? messages : []).map((msg, index) => {
                        const currSenderId = msg.sender_id || msg.sender?.id;
                        const senderEmail = msg.sender_email || msg.sender?.email;
                        const isMine = (currSenderId && currentUser?.id && currSenderId === currentUser?.id) || 
                                       (senderEmail && currentUser?.email && senderEmail.toLowerCase() === currentUser.email.toLowerCase());
                        
                        const senderName = msg.sender_name || msg.sender?.first_name || msg.sender?.email || 'Unknown';
                        const prevMsg = messages[index - 1];
                        const prevSenderEmail = prevMsg ? (prevMsg.sender_email || prevMsg.sender?.email) : null;
                        const prevSenderId = prevMsg ? (prevMsg.sender_id || prevMsg.sender?.id) : null;
                        const showHeader = index === 0 || (prevSenderId !== currSenderId && prevSenderEmail !== senderEmail);
                        
                        return (
                            <div key={msg.id || index} style={{ display: 'flex', flexDirection: 'column', alignItems: isMine ? 'flex-end' : 'flex-start', position: 'relative' }}>
                                {showHeader && (
                                    <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '0.2rem', marginLeft: isMine ? 0 : '0.5rem', marginRight: isMine ? '0.5rem' : 0 }}>
                                        {isMine ? 'You' : senderName} • {new Date(msg.created_at || new Date().toISOString()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })}
                                    </div>
                                )}
                                
                                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem', flexDirection: isMine ? 'row-reverse' : 'row', maxWidth: '85%' }}>
                                    
                                    <div 
                                        style={{ 
                                            padding: '0.6rem 0.85rem', 
                                            background: isMine ? '#6366f1' : 'white', 
                                            color: isMine ? 'white' : '#1e293b',
                                            borderRadius: '0.5rem',
                                            borderTopRightRadius: isMine && showHeader ? 0 : '0.5rem',
                                            borderTopLeftRadius: !isMine && showHeader ? 0 : '0.5rem',
                                            boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                                            border: isMine ? 'none' : '1px solid #e2e8f0',
                                            fontSize: '0.9rem',
                                            lineHeight: '1.4',
                                            wordBreak: 'break-word',
                                            position: 'relative'
                                        }}
                                    >
                                        {msg.is_deleted ? (
                                            <span style={{ fontStyle: 'italic', color: isMine ? '#e0e7ff' : '#94a3b8' }}>This message was deleted.</span>
                                        ) : (
                                            <>
                                                {msg.content}
                                                {msg.is_edited && <span style={{ fontSize: '0.65rem', opacity: 0.7, marginLeft: '0.5rem' }}>(edited)</span>}
                                                {renderAttachments(msg.attachments, isMine)}
                                            </>
                                        )}

                                        {/* Options Menu Button (Hover) */}
                                        {isMine && !msg.is_deleted && (
                                            <div 
                                                className="msg-options-btn"
                                                style={{ position: 'absolute', top: '0.2rem', right: isMine ? 'auto' : '-1.5rem', left: isMine ? '-1.5rem' : 'auto', cursor: 'pointer', color: '#94a3b8' }}
                                                onClick={() => setActiveOptions(activeOptions === msg.id ? null : msg.id)}
                                            >
                                                <MoreVertical size={14} />
                                            </div>
                                        )}
                                        
                                        {/* Options Dropdown */}
                                        {activeOptions === msg.id && (
                                            <div style={{ position: 'absolute', top: '1rem', left: '-6rem', background: 'white', borderRadius: '0.375rem', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)', border: '1px solid #e2e8f0', zIndex: 10, padding: '0.25rem' }}>
                                                <div 
                                                    style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.4rem 0.75rem', fontSize: '0.8rem', cursor: 'pointer', color: '#475569', borderRadius: '0.25rem' }}
                                                    onClick={() => handleEditStart(msg)}
                                                    onMouseEnter={(e) => e.target.style.background = '#f1f5f9'}
                                                    onMouseLeave={(e) => e.target.style.background = 'transparent'}
                                                >
                                                    <Edit2 size={12} /> Edit
                                                </div>
                                                <div 
                                                    style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.4rem 0.75rem', fontSize: '0.8rem', cursor: 'pointer', color: '#ef4444', borderRadius: '0.25rem' }}
                                                    onClick={() => handleDelete(msg.id)}
                                                    onMouseEnter={(e) => e.target.style.background = '#fef2f2'}
                                                    onMouseLeave={(e) => e.target.style.background = 'transparent'}
                                                >
                                                    <Trash2 size={12} /> Delete
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        );
                    })
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div style={{ padding: '0.75rem 1rem', background: 'white', borderTop: '1px solid #e2e8f0', position: 'relative' }}>
                
                {/* Emoji Picker */}
                {showEmojiPicker && (
                    <div ref={emojiPickerRef} style={{ position: 'absolute', bottom: '100%', left: '1rem', zIndex: 10 }}>
                        <EmojiPicker onEmojiClick={onEmojiClick} width={300} height={400} />
                    </div>
                )}
                
                {editingMessageId && (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.25rem 0.5rem', background: '#f1f5f9', borderRadius: '0.25rem', marginBottom: '0.5rem', fontSize: '0.8rem', color: '#64748b' }}>
                        <span>Editing message...</span>
                        <X size={14} style={{ cursor: 'pointer' }} onClick={() => { setEditingMessageId(null); setNewMessage(''); }} />
                    </div>
                )}
                
                {/* File Previews */}
                {attachedFiles.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.5rem', padding: '0.5rem', background: '#f8fafc', borderRadius: '0.5rem', border: '1px solid #e2e8f0' }}>
                        {attachedFiles.map((file, idx) => (
                            <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', background: 'white', padding: '0.25rem 0.5rem', borderRadius: '0.25rem', border: '1px solid #cbd5e1', fontSize: '0.75rem' }}>
                                {getFileIcon(file.type)}
                                <span style={{ maxWidth: '100px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{file.name}</span>
                                <X size={12} style={{ cursor: 'pointer', color: '#ef4444', marginLeft: '0.25rem' }} onClick={() => removeFile(idx)} />
                            </div>
                        ))}
                    </div>
                )}

                <form onSubmit={handleSend} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#f8fafc', padding: '0.25rem 0.5rem', borderRadius: '2rem', border: '1px solid #e2e8f0' }}>
                    <div style={{ display: 'flex', gap: '0.25rem', color: '#94a3b8' }}>
                        <button type="button" onClick={() => setShowEmojiPicker(!showEmojiPicker)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '0.25rem', color: showEmojiPicker ? '#6366f1' : 'inherit' }}><Smile size={18} /></button>
                        <button type="button" onClick={() => fileInputRef.current?.click()} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '0.25rem' }}><Paperclip size={18} /></button>
                        <input 
                            type="file" 
                            multiple 
                            ref={fileInputRef} 
                            onChange={handleFileSelect} 
                            style={{ display: 'none' }} 
                        />
                    </div>
                    <input 
                        type="text" 
                        value={newMessage}
                        onChange={(e) => setNewMessage(e.target.value)}
                        placeholder="Write a message..."
                        style={{ flex: 1, border: 'none', background: 'transparent', outline: 'none', padding: '0.5rem', fontSize: '0.9rem' }}
                    />
                    <button 
                        type="submit" 
                        disabled={(newMessage.trim() === '' && attachedFiles.length === 0) || isUploading}
                        style={{ 
                            background: (newMessage.trim() || attachedFiles.length > 0) ? '#6366f1' : '#cbd5e1', 
                            color: 'white', 
                            border: 'none', 
                            borderRadius: '50%', 
                            width: '32px', 
                            height: '32px', 
                            display: 'flex', 
                            alignItems: 'center', 
                            justifyContent: 'center',
                            cursor: (newMessage.trim() || attachedFiles.length > 0) && !isUploading ? 'pointer' : 'not-allowed',
                            transition: 'background 0.2s',
                            opacity: isUploading ? 0.7 : 1
                        }}
                    >
                        {isUploading ? (
                            <div style={{ width: '12px', height: '12px', border: '2px solid white', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
                        ) : (
                            <Send size={16} style={{ marginLeft: '2px' }} />
                        )}
                    </button>
                </form>
            </div>
            
            <style>{`
                .msg-options-btn { opacity: 0; transition: opacity 0.2s; }
                .msg-options-btn:hover { opacity: 1 !important; color: #475569 !important; }
                div[style*="max-width: 85%"]:hover .msg-options-btn { opacity: 0.5; }
                @keyframes spin { 100% { transform: rotate(360deg); } }
            `}</style>
        </div>
    );
};

class ContextualChatErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        console.error("ContextualChat Error:", error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div style={{ padding: '2rem', color: 'red', textAlign: 'center' }}>
                    <h4>Something went wrong in Chat.</h4>
                    <p>{this.state.error?.toString()}</p>
                </div>
            );
        }
        return <ContextualChat {...this.props} />;
    }
}

export default ContextualChatErrorBoundary;
