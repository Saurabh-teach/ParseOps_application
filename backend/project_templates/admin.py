from django.contrib import admin
from .models import ProjectTemplate, TemplateFolder, TemplateItem, GoalFolder, GoalItem

class TemplateFolderInline(admin.TabularInline):
    model = TemplateFolder
    extra = 1
    show_change_link = True
    fields = ('name', 'parent', 'order')

@admin.register(ProjectTemplate)
class ProjectTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'visibility', 'is_active', 'created_by', 'created_at', 'updated_at')
    list_filter = ('visibility', 'is_active', 'organization')
    search_fields = ('name', 'description', 'organization__name', 'created_by__email')
    ordering = ('-created_at',)
    inlines = [TemplateFolderInline]

class TemplateItemInline(admin.TabularInline):
    model = TemplateItem
    extra = 1
    fields = ('name', 'item_type', 'order')

@admin.register(TemplateFolder)
class TemplateFolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'template', 'parent', 'order', 'created_at', 'updated_at')
    list_filter = ('template', 'parent')
    search_fields = ('name', 'description', 'template__name')
    ordering = ('template', 'order', 'created_at')
    inlines = [TemplateItemInline]

@admin.register(TemplateItem)
class TemplateItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'folder', 'item_type', 'order', 'created_at', 'updated_at')
    list_filter = ('item_type', 'folder__template')
    search_fields = ('name', 'content', 'folder__name')
    ordering = ('folder', 'order', 'created_at')

class GoalItemInline(admin.TabularInline):
    model = GoalItem
    extra = 1
    fields = ('name', 'item_type', 'order')

@admin.register(GoalFolder)
class GoalFolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'goal', 'parent', 'order', 'created_at', 'updated_at')
    list_filter = ('goal', 'parent')
    search_fields = ('name', 'goal__title')
    ordering = ('goal', 'order', 'created_at')
    inlines = [GoalItemInline]

@admin.register(GoalItem)
class GoalItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'folder', 'item_type', 'order', 'created_at', 'updated_at')
    list_filter = ('item_type', 'folder__goal')
    search_fields = ('name', 'content', 'folder__name')
    ordering = ('folder', 'order', 'created_at')
