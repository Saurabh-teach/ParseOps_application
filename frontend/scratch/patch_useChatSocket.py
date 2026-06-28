import re

with open('c:/Users/saura/ParseOps/frontend/src/components/Chat/useChatSocket.js', 'r', encoding='utf-8') as f:
    content = f.read()

events_block = """            } else if (data.type === 'message_reaction') {
                if (callbacks.onReaction) {
                    callbacks.onReaction(data.message);
                }
            }
        };"""

new_events_block = """            } else if (data.type === 'message_reaction') {
                if (callbacks.onReaction) {
                    callbacks.onReaction(data.message);
                }
            } else if (data.type === 'user_presence') {
                if (callbacks.onPresence) {
                    callbacks.onPresence(data);
                }
            } else if (data.type === 'message_read') {
                if (callbacks.onMessageRead) {
                    callbacks.onMessageRead(data);
                }
            }
        };"""

if "data.type === 'user_presence'" not in content:
    content = content.replace(events_block, new_events_block)
    with open('c:/Users/saura/ParseOps/frontend/src/components/Chat/useChatSocket.js', 'w', encoding='utf-8') as f:
        f.write(content)
        
print("useChatSocket.js patched")
