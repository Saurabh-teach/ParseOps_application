with open('c:/Users/saura/ParseOps/backend/chat/views.py', 'r', encoding='utf-8') as f:
    views_content = f.read()

old_perform = """        msg = serializer.save(room=room, sender=self.request.user)
        
        # Update last read for sender"""

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
        
        # Update last read for sender"""

if old_perform in views_content:
    views_content = views_content.replace(old_perform, new_perform)
    with open('c:/Users/saura/ParseOps/backend/chat/views.py', 'w', encoding='utf-8') as f:
        f.write(views_content)
    print("Patched views.py for attachments")
