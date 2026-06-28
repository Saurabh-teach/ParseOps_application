with open('c:/Users/saura/ParseOps/backend/chat/serializers.py', 'r', encoding='utf-8') as f:
    content = f.read()

if "MessageAttachment" not in content:
    content = content.replace("from .models import ChatRoom, ChatParticipant, Message, MessageReaction", "from .models import ChatRoom, ChatParticipant, Message, MessageReaction, MessageAttachment")

attachment_serializer = """class MessageAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageAttachment
        fields = ['id', 'file', 'file_name', 'file_type', 'file_size', 'created_at']

class MessageSerializer"""

if "MessageAttachmentSerializer" not in content:
    content = content.replace("class MessageSerializer", attachment_serializer)
    
if "'attachments'" not in content:
    content = content.replace("reactions = MessageReactionSerializer(many=True, read_only=True)", "reactions = MessageReactionSerializer(many=True, read_only=True)\n    attachments = MessageAttachmentSerializer(many=True, read_only=True)")
    content = content.replace("'reactions'", "'reactions', 'attachments'")

with open('c:/Users/saura/ParseOps/backend/chat/serializers.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched serializers.py")

with open('c:/Users/saura/ParseOps/backend/chat/views.py', 'r', encoding='utf-8') as f:
    views_content = f.read()

if "MessageAttachment" not in views_content:
    views_content = views_content.replace("from .models import ChatRoom, ChatParticipant, Message, MessageReaction", "from .models import ChatRoom, ChatParticipant, Message, MessageReaction, MessageAttachment")

old_perform = """        msg = serializer.save(room=room, sender=self.request.user)
        
        # Fire notifications in background"""

new_perform = """        msg = serializer.save(room=room, sender=self.request.user)
        
        files = self.request.FILES.getlist('files')
        for f in files:
            MessageAttachment.objects.create(
                message=msg,
                file=f,
                file_name=f.name,
                file_type=f.content_type,
                file_size=f.size
            )
        
        # Fire notifications in background"""

if old_perform in views_content:
    views_content = views_content.replace(old_perform, new_perform)
    with open('c:/Users/saura/ParseOps/backend/chat/views.py', 'w', encoding='utf-8') as f:
        f.write(views_content)
    print("Patched views.py for attachments")
