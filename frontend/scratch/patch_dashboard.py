with open('c:/Users/saura/ParseOps/frontend/src/components/Dashboard.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_metric = """                <MetricCard 
                  title="Total Completed Tasks" 
                  value={data.overall_completed_tasks} 
                  icon={<CheckCircle size={24} color="#10b981" />} 
                  color="#10b981" 
                  onClick={() => onNavigate && onNavigate('tasks', { filter: 'completed' })}
                />"""

new_metric = """                <MetricCard 
                  title="Total Completed Tasks" 
                  value={data.overall_completed_tasks} 
                  icon={<CheckCircle size={24} color="#10b981" />} 
                  color="#10b981" 
                  onClick={() => onNavigate && onNavigate('tasks', { filter: 'completed' })}
                />
                <MetricCard 
                  title="Overall Pending Tasks" 
                  value={data.overall_pending_tasks ?? 0} 
                  icon={<Activity size={24} color="#f59e0b" />} 
                  color="#f59e0b" 
                  onClick={() => onNavigate && onNavigate('tasks', { filter: 'pending' })}
                />
                <MetricCard 
                  title="Overall Overdue Tasks" 
                  value={data.overall_overdue_tasks ?? 0} 
                  icon={<Activity size={24} color="#f43f5e" />} 
                  color="#f43f5e" 
                  onClick={() => onNavigate && onNavigate('tasks', { filter: 'overdue' })}
                />"""

if old_metric in content:
    content = content.replace(old_metric, new_metric)
    with open('c:/Users/saura/ParseOps/frontend/src/components/Dashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched Dashboard.jsx")
else:
    print("Not found")
