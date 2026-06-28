with open('c:/Users/saura/ParseOps/frontend/src/components/Chat/ChatLayout.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Add new state and imports
if "import { getOrganizationMembers } from '../../api';" not in content:
    content = content.replace("import api from '../../api';", "import api, { getOrganizationMembers } from '../../api';")

if "const [showNewChat, setShowNewChat] = useState(false);" not in content:
    old_state = "const [loadingRooms, setLoadingRooms] = useState(true);"
    new_state = """const [loadingRooms, setLoadingRooms] = useState(true);
    const [showNewChat, setShowNewChat] = useState(false);
    const [members, setMembers] = useState([]);
    const [isCreatingGroup, setIsCreatingGroup] = useState(false);
    const [groupName, setGroupName] = useState('');
    const [selectedMembers, setSelectedMembers] = useState([]);

    useEffect(() => {
        if (showNewChat && activeOrg?.id) {
            getOrganizationMembers(activeOrg.id).then(data => {
                // Filter out self
                const me = sessionStorage.getItem('user_id');
                setMembers(data.filter(m => m.user_id !== me));
            });
        }
    }, [showNewChat, activeOrg?.id]);

    const startDirectChat = async (userId) => {
        try {
            const res = await api.post(`org/${orgSlug}/chat/rooms/direct/`, { user_id: userId });
            setRoomId(res.data.id);
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
            if (!rooms.find(r => r.id === res.data.id)) setRooms(prev => [res.data, ...prev]);
            setShowNewChat(false);
            setIsCreatingGroup(false);
            setGroupName('');
            setSelectedMembers([]);
        } catch(e) { console.error(e); }
    };"""
    content = content.replace(old_state, new_state)

if "onClick={() => setShowNewChat(true)}" not in content:
    content = content.replace(
        "<button style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#3b82f6' }}>",
        "<button onClick={() => setShowNewChat(true)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#3b82f6' }}>"
    )

modal_code = """
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
}"""

if "{/* New Chat Modal */}" not in content:
    content = content.replace("        </div>\n    );\n}", modal_code)

with open('c:/Users/saura/ParseOps/frontend/src/components/Chat/ChatLayout.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched ChatLayout.jsx")
