from rest_framework import serializers
from .models import ProjectTemplate, TemplateFolder, TemplateItem
from users.serializers import UserSerializer

class TemplateItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateItem
        fields = '__all__'

class TemplateFolderSerializer(serializers.ModelSerializer):
    items = TemplateItemSerializer(many=True, read_only=True)
    subfolders = serializers.SerializerMethodField()

    class Meta:
        model = TemplateFolder
        fields = '__all__'

    def get_subfolders(self, obj):
        if obj.subfolders.exists():
            return TemplateFolderSerializer(obj.subfolders.all(), many=True).data
        return []

class TemplateFolderCreateSerializer(serializers.ModelSerializer):
    items = TemplateItemSerializer(many=True, required=False)
    subfolders = serializers.ListField(
        child=serializers.DictField(), required=False, write_only=True
    )

    class Meta:
        model = TemplateFolder
        fields = ['id', 'name', 'description', 'order', 'items', 'subfolders', 'goal_title']

class ProjectTemplateSerializer(serializers.ModelSerializer):
    created_by_details = UserSerializer(source='created_by', read_only=True)
    folders = serializers.SerializerMethodField()
    folder_data = serializers.ListField(
        child=serializers.DictField(), required=False, write_only=True
    )

    class Meta:
        model = ProjectTemplate
        fields = '__all__'
        read_only_fields = ('organization', 'created_by')

    def get_folders(self, obj):
        root_folders = obj.folders.filter(parent__isnull=True)
        return TemplateFolderSerializer(root_folders, many=True).data

    def create(self, validated_data):
        folders_data = validated_data.pop('folder_data', [])
        template = super().create(validated_data)
        
        def create_folder(folder_data, parent_folder=None):
            items_data = folder_data.get('items', [])
            subfolders_data = folder_data.get('subfolders', [])
            
            folder = TemplateFolder.objects.create(
                template=template,
                parent=parent_folder,
                name=folder_data.get('name', 'New Folder'),
                description=folder_data.get('description', ''),
                order=folder_data.get('order', 0),
                goal_title=folder_data.get('goal_title', '')
            )
            
            for item_data in items_data:
                TemplateItem.objects.create(
                    folder=folder,
                    item_type=item_data.get('item_type', 'document'),
                    name=item_data.get('name', 'New Item'),
                    content=item_data.get('content', {}),
                    url=item_data.get('url', ''),
                    order=item_data.get('order', 0)
                )
                
            for sub_data in subfolders_data:
                create_folder(sub_data, folder)
                
        for fd in folders_data:
            create_folder(fd)
            
        return template

    def update(self, instance, validated_data):
        folders_data = validated_data.pop('folder_data', None)
        template = super().update(instance, validated_data)
        
        if folders_data is not None:
            # Delete existing folders. Cascading deletes will remove items.
            template.folders.all().delete()
            
            def create_folder(folder_data, parent_folder=None):
                items_data = folder_data.get('items', [])
                subfolders_data = folder_data.get('subfolders', [])
                
                folder = TemplateFolder.objects.create(
                    template=template,
                    parent=parent_folder,
                    name=folder_data.get('name', 'New Folder'),
                    description=folder_data.get('description', ''),
                    order=folder_data.get('order', 0),
                    goal_title=folder_data.get('goal_title', '')
                )
                
                for item_data in items_data:
                    TemplateItem.objects.create(
                        folder=folder,
                        item_type=item_data.get('item_type', 'document'),
                        name=item_data.get('name', 'New Item'),
                        content=item_data.get('content', {}),
                        url=item_data.get('url', ''),
                        order=item_data.get('order', 0)
                    )
                    
                for sub_data in subfolders_data:
                    create_folder(sub_data, folder)
                    
            for fd in folders_data:
                create_folder(fd)
                
        return template

