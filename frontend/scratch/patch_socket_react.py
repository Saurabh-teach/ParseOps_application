import re

with open('c:/Users/saura/ParseOps/frontend/src/components/Chat/useChatSocket.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Add handler for message_reaction
handlers_block = """            else if (data.type === 'message_deleted') {
                setMessages(prev => prev.map(msg => msg.id === data.message_id ? { ...msg, content: "This message was deleted.", is_deleted: true } : msg));
            }
        };"""

new_handlers_block = """            else if (data.type === 'message_deleted') {
                setMessages(prev => prev.map(msg => msg.id === data.message_id ? { ...msg, content: "This message was deleted.", is_deleted: true } : msg));
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
        };"""

if "data.type === 'message_reaction'" not in content:
    content = content.replace(handlers_block, new_handlers_block)


funcs_block = """    const deleteMessage = useCallback((roomId, messageId) => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ 
                action: 'delete_message', 
                room_id: roomId, 
                message_id: messageId 
            }));
        }
    }, []);

    return {"""

new_funcs_block = """    const deleteMessage = useCallback((roomId, messageId) => {
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

    return {"""

if "const reactToMessage" not in content:
    content = content.replace(funcs_block, new_funcs_block)

return_block = """        markAsRead,
        editMessage,
        deleteMessage
    };"""

new_return_block = """        markAsRead,
        editMessage,
        deleteMessage,
        reactToMessage
    };"""

if "reactToMessage" not in content:
    content = content.replace(return_block, new_return_block)

with open('c:/Users/saura/ParseOps/frontend/src/components/Chat/useChatSocket.js', 'w', encoding='utf-8') as f:
    f.write(content)
print("useChatSocket.js patched for reactions")
