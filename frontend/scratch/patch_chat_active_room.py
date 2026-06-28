with open('c:/Users/saura/ParseOps/frontend/src/components/Chat/ChatLayout.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_direct = """    const startDirectChat = async (userId) => {
        try {
            const res = await api.post(`org/${orgSlug}/chat/rooms/direct/`, { user_id: userId });
            setRoomId(res.data.id);
            if (!rooms.find(r => r.id === res.data.id)) setRooms(prev => [res.data, ...prev]);
            setShowNewChat(false);
        } catch(e) { console.error(e); }
    };"""

new_direct = """    const startDirectChat = async (userId) => {
        try {
            const res = await api.post(`org/${orgSlug}/chat/rooms/direct/`, { user_id: userId });
            setRoomId(res.data.id);
            setActiveRoom(res.data);
            if (!rooms.find(r => r.id === res.data.id)) setRooms(prev => [res.data, ...prev]);
            setShowNewChat(false);
        } catch(e) { console.error(e); }
    };"""

content = content.replace(old_direct, new_direct)

old_group = """    const startGroupChat = async () => {
        if (!groupName.trim() || selectedMembers.length === 0) return;
        try {
            const res = await api.post(`org/${orgSlug}/chat/rooms/group/`, { 
                name: groupName, 
                member_ids: selectedMembers 
            });
            setRoomId(res.data.id);
            if (!rooms.find(r => r.id === res.data.id)) setRooms(prev => [res.data, ...prev]);"""

new_group = """    const startGroupChat = async () => {
        if (!groupName.trim() || selectedMembers.length === 0) return;
        try {
            const res = await api.post(`org/${orgSlug}/chat/rooms/group/`, { 
                name: groupName, 
                member_ids: selectedMembers 
            });
            setRoomId(res.data.id);
            setActiveRoom(res.data);
            if (!rooms.find(r => r.id === res.data.id)) setRooms(prev => [res.data, ...prev]);"""

content = content.replace(old_group, new_group)

with open('c:/Users/saura/ParseOps/frontend/src/components/Chat/ChatLayout.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched ChatLayout.jsx activeRoom state")
