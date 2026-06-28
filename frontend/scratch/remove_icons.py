import re

with open('c:/Users/saura/ParseOps/frontend/src/components/Chat/ChatLayout.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the Phone and Video icons from the header
header_icons_block = """                                <Search size={20} style={{ cursor: 'pointer' }} onClick={() => setShowSearch(!showSearch)} />
                                <Phone size={20} style={{ cursor: 'pointer' }} />
                                <Video size={20} style={{ cursor: 'pointer' }} />
                                <MoreVertical size={20} style={{ cursor: 'pointer' }} />"""

new_header_icons_block = """                                <Search size={20} style={{ cursor: 'pointer' }} onClick={() => setShowSearch(!showSearch)} />
                                <MoreVertical size={20} style={{ cursor: 'pointer' }} />"""

if "Phone size={20}" in content:
    content = content.replace(header_icons_block, new_header_icons_block)
    with open('c:/Users/saura/ParseOps/frontend/src/components/Chat/ChatLayout.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Icons removed successfully")
else:
    print("Icons not found or already removed")
