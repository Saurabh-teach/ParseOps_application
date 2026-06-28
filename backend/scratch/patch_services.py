with open('c:/Users/saura/ParseOps/backend/analytics/services.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_code = """    overall_total_tasks = all_tasks.count()
    overall_completed = all_tasks.filter(status='done').count()
    overall_efficiency = int((overall_completed / overall_total_tasks) * 100) if overall_total_tasks > 0 else 0"""

new_code = """    overall_total_tasks = all_tasks.count()
    overall_completed = all_tasks.filter(status='done').count()
    overall_overdue = all_tasks.exclude(status='done').filter(due_date__lt=now).count()
    overall_pending = max(0, overall_total_tasks - overall_completed - overall_overdue)
    overall_efficiency = int((overall_completed / overall_total_tasks) * 100) if overall_total_tasks > 0 else 0"""

if old_code in content:
    content = content.replace(old_code, new_code)
    
old_return = """    return {
        "role": "admin",
        "overall_total_tasks": overall_total_tasks,
        "overall_completed_tasks": overall_completed,
        "overall_efficiency": overall_efficiency,
        "total_goals": all_goals.count(),
        "total_members": total_members_count,
        "member_stats": member_stats,
    }"""

new_return = """    return {
        "role": "admin",
        "overall_total_tasks": overall_total_tasks,
        "overall_completed_tasks": overall_completed,
        "overall_pending_tasks": overall_pending,
        "overall_overdue_tasks": overall_overdue,
        "overall_efficiency": overall_efficiency,
        "total_goals": all_goals.count(),
        "total_members": total_members_count,
        "member_stats": member_stats,
    }"""

if old_return in content:
    content = content.replace(old_return, new_return)

with open('c:/Users/saura/ParseOps/backend/analytics/services.py', 'w', encoding='utf-8') as f:
    f.write(content)
