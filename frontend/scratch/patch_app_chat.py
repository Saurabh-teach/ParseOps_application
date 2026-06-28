with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

import_chat = "import ChatLayout from './components/Chat/ChatLayout';\n\n// Slim sidebar icon button"
if "import ChatLayout" not in content:
    content = content.replace("// Slim sidebar icon button", import_chat)

nav_item = "<SlimNavItem icon={<MessageSquare size={16} />} label=\"Chat\" active={activeTab === 'chat'} onClick={() => setActiveTab('chat')} />\n            <SlimNavItem icon={<Key size={16} />} label=\"Permissions\""
if "activeTab === 'chat'" not in content:
    content = content.replace("<SlimNavItem icon={<Key size={16} />} label=\"Permissions\"", nav_item)

render_block = "{activeTab === 'chat' && (() => {\n              return <ChatLayout activeOrg={selectedOrg} />;\n            })()}\n            {activeTab === 'history' && (() => {"
if "activeTab === 'chat' && (() => {" not in content:
    content = content.replace("{activeTab === 'history' && (() => {", render_block)

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched App.jsx")
