with open('c:/Users/saura/ParseOps/backend/chat/views.py', 'r', encoding='utf-8') as f:
    views_content = f.read()

old_group_send = """        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{room.id}",
            {
                "type": "chat_message","""

new_group_send = """        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_room_{room.id}",
            {
                "type": "chat_message","""

if old_group_send in views_content:
    views_content = views_content.replace(old_group_send, new_group_send)
    with open('c:/Users/saura/ParseOps/backend/chat/views.py', 'w', encoding='utf-8') as f:
        f.write(views_content)
    print("Patched views.py WebSocket group name")
