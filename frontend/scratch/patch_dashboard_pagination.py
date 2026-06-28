import re

with open('c:/Users/saura/ParseOps/frontend/src/components/Dashboard.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Add state
state_block = """  const [filters, setFilters] = useState({"""
new_state_block = """  const [memberChartPage, setMemberChartPage] = useState(0);
  const MEMBERS_PER_PAGE = 5;
  const [filters, setFilters] = useState({"""
if "const [memberChartPage" not in content:
    content = content.replace(state_block, new_state_block)

# Reset pagination when filters change
fetch_data_block = """  useEffect(() => {
    fetchDashboardData();
  }, [filters, orgId]);"""
new_fetch_data_block = """  useEffect(() => {
    fetchDashboardData();
    setMemberChartPage(0); // Reset chart pagination on filter change
  }, [filters, orgId]);"""
if "setMemberChartPage(0);" not in content:
    content = content.replace(fetch_data_block, new_fetch_data_block)

# Update the chart block
chart_block = """                  {data.member_stats.length === 0 ? (
                    <div style={{ height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', color: '#64748b', fontSize: '0.85rem' }}>
                      No members matched current filters.
                    </div>
                  ) : (
                    <ResponsiveContainer>
                      <BarChart data={data.member_stats}>
                        <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                        <YAxis stroke="#64748b" fontSize={11} />
                        <Tooltip content={<CustomTooltip />} cursor={{fill: 'transparent'}} />
                        <Bar dataKey="completed_tasks" name="Completed Tasks" fill="#10b981" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="pending_tasks" name="Pending Tasks" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="overdue_tasks" name="Overdue Tasks" fill="#f43f5e" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  )}"""

new_chart_block = """                  {data.member_stats.length === 0 ? (
                    <div style={{ height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', color: '#64748b', fontSize: '0.85rem' }}>
                      No members matched current filters.
                    </div>
                  ) : (
                    <>
                      <ResponsiveContainer height={300}>
                        <BarChart data={data.member_stats.slice(memberChartPage * MEMBERS_PER_PAGE, (memberChartPage + 1) * MEMBERS_PER_PAGE)}>
                          <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                          <YAxis stroke="#64748b" fontSize={11} />
                          <Tooltip content={<CustomTooltip />} cursor={{fill: 'transparent'}} />
                          <Bar dataKey="completed_tasks" name="Completed Tasks" fill="#10b981" radius={[4, 4, 0, 0]} />
                          <Bar dataKey="pending_tasks" name="Pending Tasks" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                          <Bar dataKey="overdue_tasks" name="Overdue Tasks" fill="#f43f5e" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                      {data.member_stats.length > MEMBERS_PER_PAGE && (
                        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1rem', marginTop: '1rem' }}>
                          <button
                            onClick={(e) => { e.stopPropagation(); setMemberChartPage(p => Math.max(0, p - 1)); }}
                            disabled={memberChartPage === 0}
                            style={{ padding: '0.25rem 0.75rem', borderRadius: '4px', border: '1px solid #cbd5e1', background: memberChartPage === 0 ? '#f1f5f9' : 'white', cursor: memberChartPage === 0 ? 'not-allowed' : 'pointer' }}
                          >
                            Previous
                          </button>
                          <span style={{ fontSize: '0.8rem', color: '#64748b' }}>
                            Page {memberChartPage + 1} of {Math.ceil(data.member_stats.length / MEMBERS_PER_PAGE)}
                          </span>
                          <button
                            onClick={(e) => { e.stopPropagation(); setMemberChartPage(p => Math.min(Math.ceil(data.member_stats.length / MEMBERS_PER_PAGE) - 1, p + 1)); }}
                            disabled={memberChartPage >= Math.ceil(data.member_stats.length / MEMBERS_PER_PAGE) - 1}
                            style={{ padding: '0.25rem 0.75rem', borderRadius: '4px', border: '1px solid #cbd5e1', background: memberChartPage >= Math.ceil(data.member_stats.length / MEMBERS_PER_PAGE) - 1 ? '#f1f5f9' : 'white', cursor: memberChartPage >= Math.ceil(data.member_stats.length / MEMBERS_PER_PAGE) - 1 ? 'not-allowed' : 'pointer' }}
                          >
                            Next
                          </button>
                        </div>
                      )}
                    </>
                  )}"""

content = content.replace(chart_block, new_chart_block)

with open('c:/Users/saura/ParseOps/frontend/src/components/Dashboard.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Dashboard.jsx patched for pagination")
