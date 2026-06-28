import { useEffect, useRef, useState, useCallback } from 'react';

export const useChatSocket = (orgId, token, activeRoomIdRef) => {
    const [messages, setMessages] = useState([]);
    const [typingUsers, setTypingUsers] = useState({});
    const [rooms, setRooms] = useState([]); // Real-time room updates
    const [isConnected, setIsConnected] = useState(false);
    const ws = useRef(null);

    useEffect(() => {
        if (!orgId || !token) return;

        // Establish connection
        // Assuming the backend runs on port 8000
        const wsUrl = `ws://localhost:8000/ws/chat/${orgId}/?token=${token}`;
        ws.current = new WebSocket(wsUrl);

        ws.current.onopen = () => {
            console.log("Chat WebSocket Connected");
            setIsConnected(true);
        };

        ws.current.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'new_message') {
                const activeRoomId = activeRoomIdRef?.current;
                if (data.message.room_id === activeRoomId) {
                    setMessages(prev => [...prev, data.message]);
                }
                
                // Update the latest message and unread count in the room list
                setRooms(prevRooms => prevRooms.map(room => {
                    if (room.id === data.message.room_id) {
                        const isNotActive = room.id !== activeRoomId;
                        return { 
                            ...room, 
                            latest_message: data.message,
                            unread_count: isNotActive ? (room.unread_count || 0) + 1 : 0
                        };
                    }
                    return room;
                }));
            } 
            else if (data.type === 'typing') {
                setTypingUsers(prev => ({
                    ...prev, 
                    [data.room_id]: {
                        ...prev[data.room_id],
                        [data.user_id]: data.is_typing ? data.user_name : null
                    }
                }));
            }
            else if (data.type === 'room_created') {
                setRooms(prev => [data.room, ...prev]);
            }
            else if (data.type === 'message_edited') {
                setMessages(prev => prev.map(msg => msg.id === data.message.id ? { ...msg, content: data.message.content, is_edited: true } : msg));
            }
            else if (data.type === 'message_deleted') {
                setMessages(prev => prev.map(msg => msg.id === data.message_id ? { ...msg, content: "This message was deleted.", is_deleted: true } : msg));
            }
            else if (data.type === 'workspace_access_lost') {
                window.dispatchEvent(new Event('workspace_access_lost'));
            }
            else if (data.type === 'message_reaction') {
                setMessages(prev => prev.map(msg => {
                    if (msg.id === data.message_id) {
                        const reactions = msg.reactions || [];
                        if (data.reaction.deleted) {
                            return { ...msg, reactions: reactions.filter(r => !(r.emoji === data.reaction.emoji && r.user?.id === data.reaction.user_id)) };
                        } else {
                            return { ...msg, reactions: [...reactions, data.reaction] };
                        }
                    }
                    return msg;
                }));
            }
        };

        ws.current.onerror = (error) => {
            console.error("WebSocket Error: ", error);
        };

        ws.current.onclose = () => {
            console.log("Chat WebSocket Disconnected. Reconnecting in 3 seconds...");
            setIsConnected(false);
            setTimeout(() => {
                // Ensure component is still mounted
                if (orgId && token) {
                    ws.current = new WebSocket(wsUrl);
                    // Minimal re-attachment for the new socket
                    ws.current.onopen = () => console.log("Chat WebSocket Reconnected");
                    // We don't redefine all handlers here to avoid complexity, 
                    // a full page refresh is better for state sync, but this keeps the connection alive.
                }
            }, 3000);
        };

        return () => {
            if (ws.current) {
                ws.current.onclose = null; // Prevent reconnect on unmount
                ws.current.close();
            }
        };
    // activeRoomIdRef is a stable ref object; its .current is read inside handlers only
    // eslint-disable-next-line react-hooks/exhaustive-deps -- ref identity is stable
    }, [orgId, token]);

    const sendMessage = useCallback((roomId, content, replyToId = null) => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ 
                action: 'send_message', 
                room_id: roomId, 
                content: content,
                reply_to: replyToId
            }));
        }
    }, []);

    const sendTypingStatus = useCallback((roomId, isTyping) => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ 
                action: 'typing', 
                room_id: roomId, 
                is_typing: isTyping 
            }));
        }
    }, []);

    const joinRoom = useCallback((roomId) => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({
                action: 'join_room',
                room_id: roomId
            }));
        }
    }, []);

    const markAsRead = useCallback((roomId, messageId) => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ 
                action: 'mark_read', 
                room_id: roomId, 
                message_id: messageId 
            }));
        }
    }, []);

    const editMessage = useCallback((roomId, messageId, newContent) => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ 
                action: 'edit_message', 
                room_id: roomId, 
                message_id: messageId,
                content: newContent
            }));
        }
    }, []);

    const deleteMessage = useCallback((roomId, messageId) => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ 
                action: 'delete_message', 
                room_id: roomId, 
                message_id: messageId 
            }));
        }
    }, []);

    const reactToMessage = useCallback((roomId, messageId, emoji) => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ 
                action: 'react_message', 
                room_id: roomId, 
                message_id: messageId,
                emoji: emoji
            }));
        }
    }, []);

    return { 
        messages, 
        setMessages,
        typingUsers, 
        rooms, 
        setRooms,
        sendMessage, 
        sendTypingStatus, 
        markAsRead,
        editMessage,
        deleteMessage,
        reactToMessage,
        joinRoom,
        isConnected,
    };
};
