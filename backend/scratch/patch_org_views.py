import re

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """        membership.is_active = False
        membership.save()
        return Response({"message": "Member removed successfully!"}, status=status.HTTP_200_OK)"""

replacement = """        membership.is_active = False
        membership.save()
        
        # Send WebSocket signal to kick the user
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"chat_user_{org.id}_{membership.user.id}",
                {
                    'type': 'workspace_access_lost',
                    'org_id': str(org.id)
                }
            )
            
        return Response({"message": "Member removed successfully!"}, status=status.HTTP_200_OK)"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("organizations/views.py patched to send WebSocket kick signal")
