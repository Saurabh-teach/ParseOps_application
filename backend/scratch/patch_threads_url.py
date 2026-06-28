import re

with open('c:/Users/saura/ParseOps/backend/chat/consumers.py', 'r', encoding='utf-8') as f:
    content = f.read()

services_import = """from .services import process_chat_notifications"""
new_services_import = """from .services import process_chat_notifications, generate_url_preview"""
if "generate_url_preview" not in content:
    content = content.replace(services_import, new_services_import)

thread_block = """            # Fire notifications in background
            threading.Thread(target=process_chat_notifications, args=(msg,)).start()"""
new_thread_block = """            # Fire notifications in background
            threading.Thread(target=process_chat_notifications, args=(msg,)).start()
            # Fetch URL preview in background
            threading.Thread(target=generate_url_preview, args=(msg,)).start()"""
if "generate_url_preview, args=(msg,)" not in content:
    content = content.replace(thread_block, new_thread_block)

with open('c:/Users/saura/ParseOps/backend/chat/consumers.py', 'w', encoding='utf-8') as f:
    f.write(content)

with open('c:/Users/saura/ParseOps/backend/chat/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

if "generate_url_preview" not in content:
    content = content.replace(services_import, new_services_import)
    content = content.replace(thread_block, new_thread_block)
    with open('c:/Users/saura/ParseOps/backend/chat/views.py', 'w', encoding='utf-8') as f:
        f.write(content)

print("consumers and views patched for url preview threading")
