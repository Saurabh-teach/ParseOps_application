with open('c:/Users/saura/ParseOps/backend/chat/models.py', 'a', encoding='utf-8') as f:
    f.write('''
class MessageAttachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='chat_attachments/%Y/%m/%d/')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100, blank=True, null=True)
    file_size = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_message_attachment'

    def __str__(self):
        return f"{self.file_name} attached to {self.message_id}"
''')
print("Patched models.py")

with open('c:/Users/saura/ParseOps/backend/chat/views.py', 'r', encoding='utf-8') as f:
    views_content = f.read()

old_direct = """        # Check if direct room already exists
        existing_rooms = ChatRoom.objects.filter(
            organization=org, room_type='direct'
        ).annotate(p_count=Count('participants')).filter(p_count=2)
        
        for room in existing_rooms:
            participants = room.participants.values_list('user_id', flat=True)
            if request.user.id in participants and target_user.id in participants:
                return Response(ChatRoomSerializer(room, context={'request': request}).data)"""

new_direct = """        # Check if direct room already exists
        existing_room = ChatRoom.objects.filter(
            organization=org, 
            room_type='direct',
            participants__user=request.user
        ).filter(
            participants__user=target_user
        ).annotate(
            p_count=Count('participants')
        ).filter(p_count=2).first()
        
        if existing_room:
            return Response(ChatRoomSerializer(existing_room, context={'request': request}).data)"""

if old_direct in views_content:
    views_content = views_content.replace(old_direct, new_direct)
    with open('c:/Users/saura/ParseOps/backend/chat/views.py', 'w', encoding='utf-8') as f:
        f.write(views_content)
    print("Patched views.py for direct chat duplicate issue")
else:
    print("Could not find old direct chat logic in views.py")
