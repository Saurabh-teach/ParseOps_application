with open('c:/Users/saura/ParseOps/frontend/src/components/Dashboard.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

custom_tooltip = """const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const memberData = payload[0].payload;
    return (
      <div style={{ background: '#fff', border: '1px solid #e2e8f0', padding: '12px', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}>
        <p style={{ margin: '0 0 8px 0', fontWeight: '600', color: '#0f172a' }}>{label}</p>
        <div style={{ display: 'flex', gap: '15px', marginBottom: '10px' }}>
            {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color, margin: '0', fontSize: '0.85rem', fontWeight: '500' }}>
                {entry.name}: {entry.value}
            </p>
            ))}
        </div>
        {memberData.task_details && memberData.task_details.length > 0 && (
          <div style={{ marginTop: '8px', borderTop: '1px solid #e2e8f0', paddingTop: '8px' }}>
            <p style={{ margin: '0 0 6px 0', fontSize: '0.75rem', fontWeight: '600', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Associated Tasks & Goals</p>
            <div style={{ maxHeight: '150px', overflowY: 'auto', paddingRight: '5px' }}>
                {memberData.task_details.map(t => (
                <div key={t.id} style={{ margin: '4px 0', display: 'flex', alignItems: 'flex-start', fontSize: '0.8rem', color: '#334155' }}>
                    <span style={{ 
                    display: 'inline-block', minWidth: '8px', width: '8px', height: '8px', borderRadius: '50%', marginRight: '6px', marginTop: '4px',
                    backgroundColor: t.category === 'completed' ? '#10b981' : (t.category === 'overdue' ? '#f43f5e' : '#f59e0b')
                    }}></span>
                    <span style={{ flex: 1, wordBreak: 'break-word', lineHeight: '1.2' }}>
                        <span style={{ fontWeight: 500 }}>{t.title}</span>
                        <br/>
                        <span style={{ color: '#94a3b8', fontSize: '0.7rem' }}>Goal: {t.goal_title}</span>
                    </span>
                </div>
                ))}
            </div>
          </div>
        )}
      </div>
    );
  }
  return null;
};

const Dashboard = ({"""

old_dash_def = "const Dashboard = ({"

if old_dash_def in content and "const CustomTooltip" not in content:
    content = content.replace(old_dash_def, custom_tooltip, 1)

old_tooltip = "<Tooltip />"
new_tooltip = "<Tooltip content={<CustomTooltip />} cursor={{fill: 'transparent'}} />"

if old_tooltip in content:
    content = content.replace(old_tooltip, new_tooltip)
    with open('c:/Users/saura/ParseOps/frontend/src/components/Dashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched Dashboard.jsx")
else:
    print("Not found")
