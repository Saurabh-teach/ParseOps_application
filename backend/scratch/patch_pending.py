with open('c:/Users/saura/ParseOps/backend/analytics/services.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_stats = '''        member_stats.append({
            "user_id": user.id,
            "name": f"{user.first_name} {user.last_name}".strip() or user.email,
            "role": membership.role,
            "total_tasks": u_total,
            "completed_tasks": u_completed,
            "overdue_tasks": u_overdue,
            "efficiency": u_efficiency
        })'''

new_stats = '''        member_stats.append({
            "user_id": user.id,
            "name": f"{user.first_name} {user.last_name}".strip() or user.email,
            "role": membership.role,
            "total_tasks": u_total,
            "completed_tasks": u_completed,
            "pending_tasks": max(0, u_total - u_completed - u_overdue),
            "overdue_tasks": u_overdue,
            "efficiency": u_efficiency
        })'''

content = content.replace(old_stats, new_stats)

with open('c:/Users/saura/ParseOps/backend/analytics/services.py', 'w', encoding='utf-8') as f:
    f.write(content)
