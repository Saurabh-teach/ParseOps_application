with open('c:/Users/saura/ParseOps/backend/analytics/services.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_code = """        u_efficiency = int((u_completed / u_total) * 100) if u_total > 0 else 0
        
        member_stats.append({
            "user_id": user.id,
            "name": f"{user.first_name} {user.last_name}".strip() or user.email,
            "role": membership.role,
            "total_tasks": u_total,
            "completed_tasks": u_completed,
            "pending_tasks": max(0, u_total - u_completed - u_overdue),
            "overdue_tasks": u_overdue,
            "efficiency": u_efficiency
        })"""

new_code = """        u_efficiency = int((u_completed / u_total) * 100) if u_total > 0 else 0
        
        task_details = []
        for t in u_tasks.select_related('goal'):
            cat = 'completed' if t.status == 'done' else ('overdue' if t.due_date and t.due_date < now else 'pending')
            task_details.append({
                "id": str(t.id),
                "title": t.title,
                "category": cat,
                "goal_title": t.goal.title if t.goal else "No Goal"
            })
            
        member_stats.append({
            "user_id": user.id,
            "name": f"{user.first_name} {user.last_name}".strip() or user.email,
            "role": membership.role,
            "total_tasks": u_total,
            "completed_tasks": u_completed,
            "pending_tasks": max(0, u_total - u_completed - u_overdue),
            "overdue_tasks": u_overdue,
            "efficiency": u_efficiency,
            "task_details": task_details
        })"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('c:/Users/saura/ParseOps/backend/analytics/services.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched backend")
else:
    print("Not found in backend")
