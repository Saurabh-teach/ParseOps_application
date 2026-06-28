import re

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

target = """            <SlimNavItem icon={<MessageSquare size={16} />} label="Chat" active={activeTab === 'chat'} onClick={() => setActiveTab('chat')} />"""

replacement = """            <SlimNavItem icon={<MessageSquare size={16} />} label="Chat" active={activeTab === 'chat'} onClick={() => setActiveTab('chat')} />
            <SlimNavItem icon={<Calendar size={16} />} label="Calendar" active={activeTab === 'calendar'} onClick={() => setActiveTab('calendar')} />"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("App.jsx patched to add Calendar to Nav")
