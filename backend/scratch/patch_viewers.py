with open('c:/Users/saura/ParseOps/backend/goals/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = """        queryset = queryset.filter(
            Q(visibility_type='organization') |
            Q(created_by=self.request.user) |
            Q(owner=self.request.user) |
            Q(visible_to=self.request.user) |
            Q(assignees=self.request.user)
        ).distinct()"""

new_filter = """        queryset = queryset.filter(
            Q(visibility_type='organization') |
            Q(sharing_option='organization') |
            Q(created_by=self.request.user) |
            Q(owner=self.request.user) |
            Q(visible_to=self.request.user) |
            Q(assignees=self.request.user) |
            Q(shared_viewers=self.request.user)
        ).distinct()"""

content = content.replace(old_filter, new_filter)

with open('c:/Users/saura/ParseOps/backend/goals/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

with open('c:/Users/saura/ParseOps/backend/analytics/services.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_analytics = """            all_goals = all_goals.filter(
                Q(visibility_type='organization') |
                Q(created_by=requesting_user) |
                Q(owner=requesting_user) |
                Q(visible_to=requesting_user) |
                Q(assignees=requesting_user)
            ).distinct()"""

new_analytics = """            all_goals = all_goals.filter(
                Q(visibility_type='organization') |
                Q(sharing_option='organization') |
                Q(created_by=requesting_user) |
                Q(owner=requesting_user) |
                Q(visible_to=requesting_user) |
                Q(assignees=requesting_user) |
                Q(shared_viewers=requesting_user)
            ).distinct()"""

content = content.replace(old_analytics, new_analytics)

with open('c:/Users/saura/ParseOps/backend/analytics/services.py', 'w', encoding='utf-8') as f:
    f.write(content)
