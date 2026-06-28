import re

with open('c:/Users/saura/ParseOps/frontend/src/components/Chat/ChatLayout.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

icons_line = "import { MessageSquare, Users, Plus, Send, Smile, Paperclip, MoreVertical, Phone, Video, Edit, Trash2, CornerUpLeft, X } from 'lucide-react';"
new_icons_line = "import { MessageSquare, Users, Plus, Send, Smile, Paperclip, MoreVertical, Phone, Video, Edit, Trash2, CornerUpLeft, X, Search } from 'lucide-react';"
if "Search } from" not in content:
    content = content.replace(icons_line, new_icons_line)

states_block = """    const [hoveredMessageId, setHoveredMessageId] = useState(null);
    const [showProfileModal, setShowProfileModal] = useState(false);
    const [selectedUser, setSelectedUser] = useState(null);
    const [showReactionPicker, setShowReactionPicker] = useState(null); // stores message ID"""
new_states_block = """    const [hoveredMessageId, setHoveredMessageId] = useState(null);
    const [showProfileModal, setShowProfileModal] = useState(false);
    const [selectedUser, setSelectedUser] = useState(null);
    const [showReactionPicker, setShowReactionPicker] = useState(null); // stores message ID
    const [showSearch, setShowSearch] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');"""
if "const [searchQuery," not in content:
    content = content.replace(states_block, new_states_block)

header_icons = """                            <div style={{ display: 'flex', gap: '15px', color: '#64748b' }}>
                                <Phone size={20} style={{ cursor: 'pointer' }} />
                                <Video size={20} style={{ cursor: 'pointer' }} />
                                <MoreVertical size={20} style={{ cursor: 'pointer' }} />
                            </div>"""
new_header_icons = """                            <div style={{ display: 'flex', gap: '15px', color: '#64748b', alignItems: 'center' }}>
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
                                <Phone size={20} style={{ cursor: 'pointer' }} />
                                <Video size={20} style={{ cursor: 'pointer' }} />
                                <MoreVertical size={20} style={{ cursor: 'pointer' }} />
                            </div>"""
if "<Search size={20}" not in content:
    content = content.replace(header_icons, new_header_icons)

messages_map = """                        <div style={{ flex: 1, padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                            {messages.map((msg, index) => {"""
new_messages_map = """                        <div style={{ flex: 1, padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                            {messages.filter(m => !searchQuery || (m.content && m.content.toLowerCase().includes(searchQuery.toLowerCase()))).map((msg, index) => {"""
if "messages.filter(m => !searchQuery" not in content:
    content = content.replace(messages_map, new_messages_map)

with open('c:/Users/saura/ParseOps/frontend/src/components/Chat/ChatLayout.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("ChatLayout.jsx patched for search")
