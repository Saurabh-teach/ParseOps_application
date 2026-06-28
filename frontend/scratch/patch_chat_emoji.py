with open('c:/Users/saura/ParseOps/frontend/src/components/Chat/ChatLayout.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Add imports
if "import EmojiPicker" not in content:
    content = content.replace("import React, { useState, useEffect } from 'react';", "import React, { useState, useEffect, useRef } from 'react';\nimport EmojiPicker from 'emoji-picker-react';")

# Add state
if "const [showEmojiPicker, setShowEmojiPicker] = useState(false);" not in content:
    content = content.replace("const [files, setFiles] = useState([]);", "const [files, setFiles] = useState([]);\n    const [showEmojiPicker, setShowEmojiPicker] = useState(false);")

# Handle Emoji click
if "const onEmojiClick =" not in content:
    emoji_func = """    const onEmojiClick = (emojiObject) => {
        setNewMessage(prevInput => prevInput + emojiObject.emoji);
        setShowEmojiPicker(false);
    };"""
    content = content.replace("const handleSendMessage = async (e) => {", f"{emoji_func}\n\n    const handleSendMessage = async (e) => {{")

# Toggle picker and attach refs
old_form = """<Smile size={20} color="#64748b" style={{ cursor: 'pointer', marginRight: '15px' }} />"""
new_form = """<div style={{ position: 'relative' }}>
                                    <Smile size={20} color="#64748b" style={{ cursor: 'pointer', marginRight: '15px' }} onClick={() => setShowEmojiPicker(prev => !prev)} />
                                    {showEmojiPicker && (
                                        <div style={{ position: 'absolute', bottom: '40px', left: 0, zIndex: 100 }}>
                                            <EmojiPicker onEmojiClick={onEmojiClick} />
                                        </div>
                                    )}
                                </div>"""

content = content.replace(old_form, new_form)

# Fix attachment URLs
old_render_msg = """                                                            <a 
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
                                                        </a>"""

new_render_msg = """                                                            <a 
                                                            key={att.id} 
                                                            href={att.file.startsWith('http') ? att.file : `http://localhost:8000${att.file}`} 
                                                            download={att.file_name}
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
                                                        </a>"""

content = content.replace(old_render_msg, new_render_msg)

with open('c:/Users/saura/ParseOps/frontend/src/components/Chat/ChatLayout.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched ChatLayout.jsx with EmojiPicker")
