import { useState, useEffect, useRef } from 'react';
import { getDashboardAnalytics, getOrganizationMembers, getOrgGoals } from '../api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { 
  Shield, Users, Target, Activity, CheckCircle, Clock, AlertCircle, 
  ChevronDown, Check, X, Search, Calendar, Briefcase, 
  TrendingUp, Sliders, RefreshCw
} from 'lucide-react';

const STATUS_OPTIONS = [
  { code: 'todo', name: 'To Do', bgActive: '#eff6ff', borderActive: '#bfdbfe', colorActive: '#1d4ed8', dotColor: '#3b82f6' },
  { code: 'in_progress', name: 'In Progress', bgActive: '#f0fdf4', borderActive: '#bbf7d0', colorActive: '#15803d', dotColor: '#22c55e' },
  { code: 'in_review', name: 'In Review', bgActive: '#faf5ff', borderActive: '#e9d5ff', colorActive: '#701a75', dotColor: '#d946ef' },
  { code: 'testing', name: 'Testing', bgActive: '#fdf4ff', borderActive: '#f3e8ff', colorActive: '#6b21a8', dotColor: '#a855f7' },
  { code: 'done', name: 'Done', bgActive: '#ecfdf5', borderActive: '#a7f3d0', colorActive: '#047857', dotColor: '#10b981' },
  { code: 'backlog', name: 'Backlog', bgActive: '#f8fafc', borderActive: '#cbd5e1', colorActive: '#475569', dotColor: '#64748b' },
  { code: 'overdue', name: 'Overdue', bgActive: '#fff1f2', borderActive: '#fecdd3', colorActive: '#be123c', dotColor: '#f43f5e' }
];

const CustomTooltip = ({ active, payload, label }) => {
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

export default function Dashboard({ activeOrg, onNavigate, joinRequestsCount }) {
  const [data, setData] = useState(null);
  const [loadedOrgId, setLoadedOrgId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState('');
  


  // Dropdown & Lists State
  const [members, setMembers] = useState([]);
  const [goals, setGoals] = useState([]);
  const [openDropdown, setOpenDropdown] = useState(null); // 'members', 'priorities', 'date_range', 'goal', 'task_types', 'more'
  
  // Search inputs inside dropdowns
  const [memberSearch, setMemberSearch] = useState('');
  const [goalSearch, setGoalSearch] = useState('');

  // Filters State
  const [memberChartPage, setMemberChartPage] = useState(0);
  const MEMBERS_PER_PAGE = 5;
  const [filters, setFilters] = useState({
    members: [],        // array of user IDs
    statuses: [],       // array of status codes
    priorities: [],     // array of priority codes
    date_range: 'all_time', // default to all time
    start_date: '',
    end_date: '',
    goal: 'all',
    task_types: [],     // array of issue types
    assignee_type: 'all_tasks', // my_tasks, created_tasks, all_tasks
    overdue_status: '', // only_overdue, not_overdue, ''
    completion_rate: '' // high, medium, low, ''
  });
  const hasLoadedAnalyticsRef = useRef(false);

  // Fetch Members & Goals when organization changes
  useEffect(() => {
    if (activeOrg) {
      hasLoadedAnalyticsRef.current = false;
      getOrganizationMembers(activeOrg.id)
        .then(res => setMembers(res || []))
        .catch(err => console.error('Failed to load members:', err));
        
      getOrgGoals(activeOrg.slug)
        .then(res => setGoals(res || []))
        .catch(err => console.error('Failed to load goals:', err));
      
      // Reset filters on org change
      resetFilters();
    }
  }, [activeOrg]);

  // Fetch Dashboard Analytics with filters in real-time
  useEffect(() => {
    if (!activeOrg) return;

    let cancelled = false;

    const params = {};
    if (filters.members.length > 0) params.members = filters.members.join(',');
    if (filters.statuses.length > 0) params.statuses = filters.statuses.join(',');
    if (filters.priorities.length > 0) params.priorities = filters.priorities.join(',');
    if (filters.date_range) params.date_range = filters.date_range;
    if (filters.date_range === 'custom') {
      if (filters.start_date) params.start_date = filters.start_date;
      if (filters.end_date) params.end_date = filters.end_date;
    }
    if (filters.goal !== 'all') params.goal = filters.goal;
    if (filters.task_types.length > 0) params.task_types = filters.task_types.join(',');
    if (filters.assignee_type !== 'all_tasks') params.assignee_type = filters.assignee_type;
    if (filters.overdue_status) params.overdue_status = filters.overdue_status;
    if (filters.completion_rate) params.completion_rate = filters.completion_rate;

    const fetchAnalytics = async () => {
      if (!hasLoadedAnalyticsRef.current) {
        setLoading(true);
      } else {
        setIsUpdating(true);
      }

      try {
        const res = await getDashboardAnalytics(activeOrg.id, params);
        if (cancelled) return;
        setData(res);
        setLoadedOrgId(activeOrg.id);
        setError('');
        hasLoadedAnalyticsRef.current = true;
      } catch (err) {
        if (cancelled) return;
        console.error(err);
        setError('Failed to load dashboard analytics');
      } finally {
        if (!cancelled) {
          setLoading(false);
          setIsUpdating(false);
        }
      }
    };

    fetchAnalytics();
    return () => { cancelled = true; };
  }, [activeOrg, filters]);

  function resetFilters() {
    setFilters({
      members: [],
      statuses: [],
      priorities: [],
      date_range: 'all_time',
      start_date: '',
      end_date: '',
      goal: 'all',
      task_types: [],
      assignee_type: 'all_tasks',
      overdue_status: '',
      completion_rate: ''
    });
    setOpenDropdown(null);
  }

  const toggleDropdown = (name) => {
    setOpenDropdown(openDropdown === name ? null : name);
  };

  const handleMultiSelect = (key, value) => {
    setFilters(prev => {
      const current = prev[key] || [];
      const updated = current.includes(value)
        ? current.filter(item => item !== value)
        : [...current, value];
      return { ...prev, [key]: updated };
    });
  };

  const handleSingleSelect = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  // Helper to check if any filter is active
  const hasActiveFilters = 
    filters.members.length > 0 ||
    filters.statuses.length > 0 ||
    filters.priorities.length > 0 ||
    filters.date_range !== 'all_time' ||
    filters.goal !== 'all' ||
    filters.task_types.length > 0 ||
    filters.assignee_type !== 'all_tasks' ||
    filters.overdue_status !== '' ||
    filters.completion_rate !== '';

  const isStaleData = activeOrg && loadedOrgId !== activeOrg.id;

  if (loading || isStaleData) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '100%', color: '#6366f1', gap: '12px' }}>
        <RefreshCw className="animate-spin" size={32} />
        <span style={{ fontWeight: 600, fontSize: '1rem' }}>Loading Analytics...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '3rem 2rem', color: '#ef4444', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
        <AlertCircle size={40} />
        <span style={{ fontWeight: 600, fontSize: '1.1rem' }}>{error}</span>
        <button className="btn-primary" onClick={resetFilters} style={{ marginTop: '12px' }}>Reset Filters</button>
      </div>
    );
  }

  if (!data) return null;

  // Filter lists & lookups
  const activeMembersLookup = members.reduce((acc, m) => {
    if (m.user) acc[m.user.id] = `${m.user.first_name || ''} ${m.user.last_name || ''}`.trim() || m.user.email;
    return acc;
  }, {});

  const activeGoalsLookup = goals.reduce((acc, g) => {
    acc[g.id] = g.title;
    return acc;
  }, {});

  // Date range display helpers
  const dateRangeNames = {
    'all_time': 'All Time',
    'this_week': 'This Week',
    'this_month': 'This Month',
    'last_30_days': 'Last 30 Days',
    'last_quarter': 'Last Quarter',
    'custom': 'Custom Range'
  };

  return (
    <div className="content-scroll" style={{ backgroundColor: '#f8fafc', minHeight: '100%', padding: '1.5rem', position: 'relative' }}>
      
      {/* Invisible overlay to close dropdowns when clicking outside */}
      {openDropdown && (
        <div 
          onClick={() => setOpenDropdown(null)} 
          style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 40, cursor: 'default' }}
        />
      )}

      <div style={{ maxWidth: '1240px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        
        {/* ================= HEADER & STATUS SECTION ================= */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#0f172a', margin: 0, letterSpacing: '-0.025em', display: 'flex', alignItems: 'center', gap: '12px' }}>
              Dashboard & Analytics
              {isUpdating && <RefreshCw size={18} className="animate-spin" style={{ color: '#6366f1' }} />}
            </h1>
            <p style={{ color: '#64748b', fontSize: '0.9rem', marginTop: '4px' }}>
              Real-time progress overview for <strong>{activeOrg?.name}</strong>
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', backgroundColor: '#eef2ff', padding: '8px 16px', borderRadius: '99px', border: '1px solid #e0e7ff' }}>
              <Shield size={15} color="#6366f1" />
              <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#4f46e5', textTransform: 'capitalize' }}>
                {data.role} View
              </span>
            </div>
          </div>
        </div>



        {/* ================= FILTERS TOP BAR (ClickUp & Power BI Inspired) ================= */}
        <div style={{ 
          backgroundColor: '#ffffff', 
          border: '1px solid #e2e8f0', 
          borderRadius: '12px', 
          padding: '1rem', 
          display: 'flex', 
          flexDirection: 'column', 
          gap: '1rem',
          boxShadow: '0 1px 3px rgba(0,0,0,0.02)'
        }}>
          
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
            {/* Filters Row */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', zIndex: 45 }}>
              
              {/* Member Filter (Admin/Owner Only) */}
              {(data.role === 'admin' || data.role === 'owner') && (
                <DropdownFilter
                  label={filters.members.length === 0 ? "All Members" : `Members (${filters.members.length})`}
                  icon={<Users size={14} />}
                  isOpen={openDropdown === 'members'}
                  isActive={filters.members.length > 0}
                  onClick={() => toggleDropdown('members')}
                >
                  <div style={{ padding: '4px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', border: '1px solid #e2e8f0', borderRadius: '6px', padding: '4px 8px', backgroundColor: '#f8fafc' }}>
                      <Search size={12} color="#94a3b8" />
                      <input 
                        type="text" 
                        placeholder="Search member..."
                        value={memberSearch}
                        onChange={e => setMemberSearch(e.target.value)}
                        style={{ border: 'none', background: 'none', fontSize: '0.8rem', width: '100%', outline: 'none', padding: 0 }}
                      />
                    </div>
                    <div style={{ maxHeight: '180px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                      {members
                        .filter(m => {
                          const name = `${m.user?.first_name || ''} ${m.user?.last_name || ''}`.toLowerCase();
                          const email = (m.user?.email || '').toLowerCase();
                          return name.includes(memberSearch.toLowerCase()) || email.includes(memberSearch.toLowerCase());
                        })
                        .map(m => {
                          const userId = m.user?.id;
                          const userName = `${m.user?.first_name || ''} ${m.user?.last_name || ''}`.trim() || m.user?.email;
                          const isSelected = filters.members.includes(userId);
                          return (
                            <div 
                              key={userId} 
                              onClick={() => handleMultiSelect('members', userId)}
                              style={{
                                display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 8px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.8rem',
                                backgroundColor: isSelected ? '#f5f3ff' : 'transparent',
                                color: isSelected ? '#6d28d9' : '#334155',
                                fontWeight: isSelected ? 600 : 400
                              }}
                              onMouseEnter={e => e.currentTarget.style.backgroundColor = isSelected ? '#f5f3ff' : '#f1f5f9'}
                              onMouseLeave={e => e.currentTarget.style.backgroundColor = isSelected ? '#f5f3ff' : 'transparent'}
                            >
                              <span style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', maxWidth: '160px' }}>{userName}</span>
                              {isSelected && <Check size={12} />}
                            </div>
                          );
                        })}
                    </div>
                  </div>
                </DropdownFilter>
              )}

              {/* Priority Filter */}
              <DropdownFilter
                label={filters.priorities.length === 0 ? "All Priorities" : `Priority (${filters.priorities.length})`}
                icon={<TrendingUp size={14} />}
                isOpen={openDropdown === 'priorities'}
                isActive={filters.priorities.length > 0}
                onClick={() => toggleDropdown('priorities')}
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                  {[
                    { code: 'low', name: 'Low' },
                    { code: 'medium', name: 'Medium' },
                    { code: 'high', name: 'High' }
                  ].map(p => {
                    const isSelected = filters.priorities.includes(p.code);
                    return (
                      <div 
                        key={p.code} 
                        onClick={() => handleMultiSelect('priorities', p.code)}
                        style={{
                          display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 10px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.8rem',
                          backgroundColor: isSelected ? '#f5f3ff' : 'transparent',
                          color: isSelected ? '#6d28d9' : '#334155',
                          fontWeight: isSelected ? 600 : 400
                        }}
                        onMouseEnter={e => e.currentTarget.style.backgroundColor = isSelected ? '#f5f3ff' : '#f1f5f9'}
                        onMouseLeave={e => e.currentTarget.style.backgroundColor = isSelected ? '#f5f3ff' : 'transparent'}
                      >
                        <span>{p.name}</span>
                        {isSelected && <Check size={12} />}
                      </div>
                    );
                  })}
                </div>
              </DropdownFilter>

              {/* Date Range Filter */}
              <DropdownFilter
                label={dateRangeNames[filters.date_range]}
                icon={<Calendar size={14} />}
                isOpen={openDropdown === 'date_range'}
                isActive={filters.date_range !== ''}
                onClick={() => toggleDropdown('date_range')}
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {Object.entries(dateRangeNames).map(([code, name]) => {
                    const isSelected = filters.date_range === code;
                    return (
                      <div 
                        key={code} 
                        onClick={() => handleSingleSelect('date_range', code)}
                        style={{
                          display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 10px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.8rem',
                          backgroundColor: isSelected ? '#f5f3ff' : 'transparent',
                          color: isSelected ? '#6d28d9' : '#334155',
                          fontWeight: isSelected ? 600 : 400
                        }}
                        onMouseEnter={e => e.currentTarget.style.backgroundColor = isSelected ? '#f5f3ff' : '#f1f5f9'}
                        onMouseLeave={e => e.currentTarget.style.backgroundColor = isSelected ? '#f5f3ff' : 'transparent'}
                      >
                        <span>{name}</span>
                        {isSelected && <Check size={12} />}
                      </div>
                    );
                  })}

                  {filters.date_range === 'custom' && (
                    <div style={{ borderTop: '1px solid #e2e8f0', marginTop: '8px', paddingTop: '8px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        <span style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600 }}>Start Date</span>
                        <input 
                          type="date"
                          value={filters.start_date}
                          onChange={e => handleSingleSelect('start_date', e.target.value)}
                          style={{ fontSize: '0.8rem', padding: '4px 6px', border: '1px solid #cbd5e1', borderRadius: '4px', outline: 'none' }}
                        />
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        <span style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600 }}>End Date</span>
                        <input 
                          type="date"
                          value={filters.end_date}
                          onChange={e => handleSingleSelect('end_date', e.target.value)}
                          style={{ fontSize: '0.8rem', padding: '4px 6px', border: '1px solid #cbd5e1', borderRadius: '4px', outline: 'none' }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </DropdownFilter>

              {/* Goal Filter */}
              <DropdownFilter
                label={filters.goal === 'all' ? "All Goals" : (activeGoalsLookup[filters.goal] || "Goal Selected")}
                icon={<Target size={14} />}
                isOpen={openDropdown === 'goal'}
                isActive={filters.goal !== 'all'}
                onClick={() => toggleDropdown('goal')}
              >
                <div style={{ padding: '4px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', border: '1px solid #e2e8f0', borderRadius: '6px', padding: '4px 8px', backgroundColor: '#f8fafc' }}>
                    <Search size={12} color="#94a3b8" />
                    <input 
                      type="text" 
                      placeholder="Search goal..."
                      value={goalSearch}
                      onChange={e => setGoalSearch(e.target.value)}
                      style={{ border: 'none', background: 'none', fontSize: '0.8rem', width: '100%', outline: 'none', padding: 0 }}
                    />
                  </div>
                  <div style={{ maxHeight: '180px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                    <div 
                      onClick={() => handleSingleSelect('goal', 'all')}
                      style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 8px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.8rem',
                        backgroundColor: filters.goal === 'all' ? '#f5f3ff' : 'transparent',
                        color: filters.goal === 'all' ? '#6d28d9' : '#334155',
                        fontWeight: filters.goal === 'all' ? 600 : 400
                      }}
                      onMouseEnter={e => e.currentTarget.style.backgroundColor = filters.goal === 'all' ? '#f5f3ff' : '#f1f5f9'}
                      onMouseLeave={e => e.currentTarget.style.backgroundColor = filters.goal === 'all' ? '#f5f3ff' : 'transparent'}
                    >
                      <span>All Goals</span>
                      {filters.goal === 'all' && <Check size={12} />}
                    </div>
                    {goals
                      .filter(g => g.title.toLowerCase().includes(goalSearch.toLowerCase()))
                      .map(g => {
                        const isSelected = filters.goal === g.id;
                        return (
                          <div 
                            key={g.id} 
                            onClick={() => handleSingleSelect('goal', g.id)}
                            style={{
                              display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 8px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.8rem',
                              backgroundColor: isSelected ? '#f5f3ff' : 'transparent',
                              color: isSelected ? '#6d28d9' : '#334155',
                              fontWeight: isSelected ? 600 : 400
                            }}
                            onMouseEnter={e => e.currentTarget.style.backgroundColor = isSelected ? '#f5f3ff' : '#f1f5f9'}
                            onMouseLeave={e => e.currentTarget.style.backgroundColor = isSelected ? '#f5f3ff' : 'transparent'}
                          >
                            <span style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', maxWidth: '160px' }}>{g.title}</span>
                            {isSelected && <Check size={12} />}
                          </div>
                        );
                      })}
                  </div>
                </div>
              </DropdownFilter>

              {/* Task Type Filter */}
              <DropdownFilter
                label={filters.task_types.length === 0 ? "All Types" : `Types (${filters.task_types.length})`}
                icon={<Briefcase size={14} />}
                isOpen={openDropdown === 'task_types'}
                isActive={filters.task_types.length > 0}
                onClick={() => toggleDropdown('task_types')}
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                  {[
                    { code: 'task', name: 'Task' },
                    { code: 'story', name: 'Story' },
                    { code: 'bug', name: 'Bug' },
                    { code: 'epic', name: 'Epic' }
                  ].map(t => {
                    const isSelected = filters.task_types.includes(t.code);
                    return (
                      <div 
                        key={t.code} 
                        onClick={() => handleMultiSelect('task_types', t.code)}
                        style={{
                          display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 10px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.8rem',
                          backgroundColor: isSelected ? '#f5f3ff' : 'transparent',
                          color: isSelected ? '#6d28d9' : '#334155',
                          fontWeight: isSelected ? 600 : 400
                        }}
                        onMouseEnter={e => e.currentTarget.style.backgroundColor = isSelected ? '#f5f3ff' : '#f1f5f9'}
                        onMouseLeave={e => e.currentTarget.style.backgroundColor = isSelected ? '#f5f3ff' : 'transparent'}
                      >
                        <span>{t.name}</span>
                        {isSelected && <Check size={12} />}
                      </div>
                    );
                  })}
                </div>
              </DropdownFilter>

            </div>

            {/* Advanced Filters Button */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', zIndex: 45 }}>
              <DropdownFilter
                label="More Filters"
                icon={<Sliders size={14} />}
                isOpen={openDropdown === 'more'}
                isActive={filters.assignee_type !== 'all_tasks' || filters.overdue_status !== '' || filters.completion_rate !== ''}
                onClick={() => toggleDropdown('more')}
                badgeCount={(filters.assignee_type !== 'all_tasks' ? 1 : 0) + (filters.overdue_status !== '' ? 1 : 0) + (filters.completion_rate !== '' ? 1 : 0)}
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', minWidth: '240px', padding: '4px' }}>
                  {/* Assignee Type */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#475569' }}>Assignee Type</span>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      {[
                        { code: 'all_tasks', name: 'All Tasks' },
                        { code: 'my_tasks', name: 'My Tasks' },
                        { code: 'created_tasks', name: 'Tasks I Created' }
                      ].map(a => {
                        const isSelected = filters.assignee_type === a.code;
                        return (
                          <div 
                            key={a.code}
                            onClick={() => handleSingleSelect('assignee_type', a.code)}
                            style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.8rem', padding: '4px 6px', borderRadius: '4px', backgroundColor: isSelected ? '#f8fafc' : 'transparent' }}
                          >
                            <input type="radio" checked={isSelected} readOnly style={{ accentColor: '#6366f1' }} />
                            <span style={{ color: isSelected ? '#1e293b' : '#64748b', fontWeight: isSelected ? 600 : 400 }}>{a.name}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Overdue Filter */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', borderTop: '1px solid #f1f5f9', paddingTop: '10px' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#475569' }}>Overdue Filter</span>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      {[
                        { code: '', name: 'All' },
                        { code: 'only_overdue', name: 'Only Overdue' },
                        { code: 'not_overdue', name: 'Not Overdue' }
                      ].map(o => {
                        const isSelected = filters.overdue_status === o.code;
                        return (
                          <div 
                            key={o.code}
                            onClick={() => handleSingleSelect('overdue_status', o.code)}
                            style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.8rem', padding: '4px 6px', borderRadius: '4px', backgroundColor: isSelected ? '#f8fafc' : 'transparent' }}
                          >
                            <input type="radio" checked={isSelected} readOnly style={{ accentColor: '#6366f1' }} />
                            <span style={{ color: isSelected ? '#1e293b' : '#64748b', fontWeight: isSelected ? 600 : 400 }}>{o.name}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Completion Rate Filter (Admin/Owner Only) */}
                  {(data.role === 'admin' || data.role === 'owner') && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', borderTop: '1px solid #f1f5f9', paddingTop: '10px' }}>
                      <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#475569' }}>Completion Rate / Performers</span>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        {[
                          { code: '', name: 'All Members' },
                          { code: 'high', name: 'High Performers (≥70%)' },
                          { code: 'medium', name: 'Medium Performers (30%-69%)' },
                          { code: 'low', name: 'Low Performers (<30%)' }
                        ].map(c => {
                          const isSelected = filters.completion_rate === c.code;
                          return (
                            <div 
                              key={c.code}
                              onClick={() => handleSingleSelect('completion_rate', c.code)}
                              style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.8rem', padding: '4px 6px', borderRadius: '4px', backgroundColor: isSelected ? '#f8fafc' : 'transparent' }}
                            >
                              <input type="radio" checked={isSelected} readOnly style={{ accentColor: '#6366f1' }} />
                              <span style={{ color: isSelected ? '#1e293b' : '#64748b', fontWeight: isSelected ? 600 : 400 }}>{c.name}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </DropdownFilter>

              {hasActiveFilters && (
                <button
                  onClick={resetFilters}
                  style={{
                    display: 'flex', alignItems: 'center', gap: '4px', padding: '6px 12px', fontSize: '0.8rem', fontWeight: 600, color: '#ef4444', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', cursor: 'pointer', height: '36px', transition: 'all 0.2s'
                  }}
                  onMouseEnter={e => e.currentTarget.style.backgroundColor = '#fee2e2'}
                  onMouseLeave={e => e.currentTarget.style.backgroundColor = '#fef2f2'}
                >
                  <XCircle size={14} />
                  Reset
                </button>
              )}
            </div>
          </div>

          {/* Status Filter Chips Row (Prominent Top Bar UI Accent) */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', borderTop: '1px solid #f1f5f9', paddingTop: '0.75rem' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#64748b', marginRight: '4px' }}>Status:</span>
            {STATUS_OPTIONS.map(s => {
              const isSelected = filters.statuses.includes(s.code);
              return (
                <button
                  key={s.code}
                  onClick={() => handleMultiSelect('statuses', s.code)}
                  style={{
                    padding: '5px 12px',
                    fontSize: '0.78rem',
                    fontWeight: 600,
                    borderRadius: '99px',
                    cursor: 'pointer',
                    border: '1px solid',
                    transition: 'all 0.15s ease-in-out',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    backgroundColor: isSelected ? s.bgActive : '#ffffff',
                    borderColor: isSelected ? s.borderActive : '#e2e8f0',
                    color: isSelected ? s.colorActive : '#64748b',
                    boxShadow: isSelected ? '0 1px 2px rgba(0,0,0,0.03)' : 'none'
                  }}
                  onMouseEnter={e => {
                    if (!isSelected) e.currentTarget.style.backgroundColor = '#f1f5f9';
                  }}
                  onMouseLeave={e => {
                    if (!isSelected) e.currentTarget.style.backgroundColor = '#ffffff';
                  }}
                >
                  <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: s.dotColor }} />
                  {s.name}
                  {isSelected && <Check size={12} />}
                </button>
              );
            })}
          </div>

          {/* Active Filters Summary Badges (Premium UX Component) */}
          {hasActiveFilters && (
            <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '0.5rem', display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', marginRight: '4px' }}>Active Filters:</span>
              
              {filters.members.map(userId => (
                <FilterBadge 
                  key={userId} 
                  label={`Member: ${activeMembersLookup[userId] || 'User'}`} 
                  onRemove={() => handleMultiSelect('members', userId)} 
                />
              ))}

              {filters.statuses.map(s => {
                const opt = STATUS_OPTIONS.find(o => o.code === s);
                return (
                  <FilterBadge 
                    key={s} 
                    label={`Status: ${opt ? opt.name : s.toUpperCase()}`} 
                    onRemove={() => handleMultiSelect('statuses', s)} 
                  />
                );
              })}

              {filters.priorities.map(p => (
                <FilterBadge 
                  key={p} 
                  label={`Priority: ${p.toUpperCase()}`} 
                  onRemove={() => handleMultiSelect('priorities', p)} 
                />
              ))}

              {filters.date_range && filters.date_range !== 'all_time' && (
                <FilterBadge 
                  label={`Date: ${dateRangeNames[filters.date_range]}`} 
                  onRemove={() => handleSingleSelect('date_range', 'all_time')} 
                />
              )}

              {filters.goal !== 'all' && (
                <FilterBadge 
                  label={`Goal: ${activeGoalsLookup[filters.goal] || 'Goal'}`} 
                  onRemove={() => handleSingleSelect('goal', 'all')} 
                />
              )}

              {filters.task_types.map(t => (
                <FilterBadge 
                  key={t} 
                  label={`Type: ${t.toUpperCase()}`} 
                  onRemove={() => handleMultiSelect('task_types', t)} 
                />
              ))}

              {filters.assignee_type !== 'all_tasks' && (
                <FilterBadge 
                  label={`Assignee: ${filters.assignee_type === 'my_tasks' ? 'My Tasks' : 'Created By Me'}`} 
                  onRemove={() => handleSingleSelect('assignee_type', 'all_tasks')} 
                />
              )}

              {filters.overdue_status !== '' && (
                <FilterBadge 
                  label={`Overdue: ${filters.overdue_status === 'only_overdue' ? 'Only Overdue' : 'Not Overdue'}`} 
                  onRemove={() => handleSingleSelect('overdue_status', '')} 
                />
              )}

              {filters.completion_rate !== '' && (
                <FilterBadge 
                  label={`Performers: ${filters.completion_rate.toUpperCase()}`} 
                  onRemove={() => handleSingleSelect('completion_rate', '')} 
                />
              )}
            </div>
          )}
        </div>

        {/* ================= MAIN DASHBOARD BODY (Fade-in animations & responsive grid) ================= */}
        <div style={{
          opacity: isUpdating ? 0.65 : 1,
          filter: isUpdating ? 'blur(0.5px)' : 'none',
          transition: 'all 0.25s ease-in-out',
          pointerEvents: isUpdating ? 'none' : 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.5rem'
        }}>

          {/* ================= NORMAL MEMBER VIEW ================= */}
          {data.role === 'member' && (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.5rem' }}>
                <MetricCard 
                  title="Your Assigned Tasks" 
                  value={data.total_tasks} 
                  icon={<Activity size={24} color="#6366f1" />} 
                  color="#6366f1" 
                  onClick={() => onNavigate && onNavigate('tasks')}
                />
                <MetricCard 
                  title="Tasks Completed" 
                  value={data.completed_tasks} 
                  icon={<CheckCircle size={24} color="#10b981" />} 
                  color="#10b981" 
                  onClick={() => onNavigate && onNavigate('tasks', { filter: 'completed' })}
                />
                <MetricCard 
                  title="Overdue Tasks" 
                  value={data.overdue_tasks} 
                  icon={<Clock size={24} color="#f43f5e" />} 
                  color="#f43f5e" 
                  onClick={() => onNavigate && onNavigate('tasks', { filter: 'overdue' })}
                />
                <MetricCard 
                  title="Your Efficiency Rate" 
                  value={`${data.efficiency}%`} 
                  icon={<Target size={24} color="#f59e0b" />} 
                  color="#f59e0b" 
                  onClick={() => onNavigate && onNavigate('profile')}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem' }}>
                {/* Task Breakdown Pie Chart */}
                <div 
                  style={{ 
                    backgroundColor: '#fff', 
                    padding: '1.5rem', 
                    borderRadius: '16px', 
                    border: '1px solid #e2e8f0', 
                    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                    transition: 'transform 0.2s, box-shadow 0.2s'
                  }}
                  className="interactive-dashboard-card"
                >
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#0f172a', marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>Your Task Status Breakdown</span>
                    <span style={{ fontSize: '0.75rem', color: '#6366f1', fontWeight: 500 }}>Click slice to View List</span>
                  </h3>
                  <div style={{ height: 260, width: '100%' }}>
                    {data.completed_tasks + data.in_progress_tasks + data.overdue_tasks === 0 ? (
                      <div style={{ height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', color: '#64748b', fontSize: '0.85rem' }}>
                        No filtered tasks for status breakdown.
                      </div>
                    ) : (
                      <ResponsiveContainer>
                        <PieChart>
                          <Pie 
                            data={[
                              { name: 'Completed', value: data.completed_tasks, filterCode: 'completed', color: '#10b981' },
                              { name: 'In Progress', value: data.in_progress_tasks, filterCode: 'all', color: '#6366f1' },
                              { name: 'Overdue', value: data.overdue_tasks, filterCode: 'overdue', color: '#f43f5e' }
                            ].filter(item => item.value > 0)} 
                            dataKey="value" 
                            outerRadius={80}
                            innerRadius={50}
                            paddingAngle={5}
                            onClick={(entry) => {
                              if (onNavigate) onNavigate('tasks', { filter: entry.filterCode });
                            }}
                            style={{ cursor: 'pointer' }}
                          >
                            {[
                              { name: 'Completed', value: data.completed_tasks, color: '#10b981' },
                              { name: 'In Progress', value: data.in_progress_tasks, color: '#6366f1' },
                              { name: 'Overdue', value: data.overdue_tasks, color: '#f43f5e' }
                            ].filter(item => item.value > 0).map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <Tooltip content={<CustomTooltip />} cursor={{fill: 'transparent'}} />
                        </PieChart>
                      </ResponsiveContainer>
                    )}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'center', gap: '1.5rem', marginTop: '1rem', fontSize: '0.85rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><div style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: '#10b981' }}></div> Completed</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><div style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: '#6366f1' }}></div> In Progress</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><div style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: '#f43f5e' }}></div> Overdue</div>
                  </div>
                </div>

                {/* Goals Summary Card */}
                <div 
                  onClick={() => onNavigate && onNavigate('goals')}
                  style={{ 
                    backgroundColor: '#fff', 
                    padding: '1.5rem', 
                    borderRadius: '16px', 
                    border: '1px solid #e2e8f0', 
                    boxShadow: '0 1px 3px rgba(0,0,0,0.05)', 
                    display: 'flex', 
                    flexDirection: 'column', 
                    justifyContent: 'center', 
                    alignItems: 'center', 
                    textAlign: 'center',
                    cursor: 'pointer',
                    transition: 'transform 0.2s, box-shadow 0.2s'
                  }}
                  className="interactive-dashboard-card"
                >
                  <div style={{ width: 72, height: 72, borderRadius: '50%', backgroundColor: '#eef2ff', display: 'flex', alignItems: 'center', justifyItems: 'center', justifyContent: 'center', marginBottom: '1.5rem' }}>
                    <Target size={36} color="#6366f1" />
                  </div>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a', margin: '0 0 8px 0' }}>Goals Ecosystem</h3>
                  <p style={{ color: '#64748b', fontSize: '0.9rem', maxWidth: '300px', lineHeight: 1.5, marginBottom: '8px' }}>
                    You are actively contributing to <strong>{data.goals_involved}</strong> goals in this workspace. Align your tasks to achieve key results!
                  </p>
                  <span style={{ fontSize: '0.8rem', color: '#6366f1', fontWeight: 600 }}>Click to View Goals →</span>
                </div>
              </div>
            </>
          )}

          {/* ================= ADMIN & OWNER VIEW ================= */}
          {(data.role === 'admin' || data.role === 'owner') && (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.5rem' }}>
                <MetricCard 
                  title="Active Members" 
                  value={data.total_members ?? (data.member_stats?.length || 0)} 
                  icon={<Users size={24} color="#6366f1" />} 
                  color="#6366f1" 
                  onClick={() => onNavigate && onNavigate('members')}
                />
                <MetricCard 
                  title="Pending Requests" 
                  value={joinRequestsCount} 
                  icon={<Shield size={24} color="#f59e0b" />} 
                  color="#f59e0b" 
                  onClick={() => onNavigate && onNavigate('permissions')}
                />
                <MetricCard 
                  title="Overall Workspace Tasks" 
                  value={data.overall_total_tasks} 
                  icon={<Activity size={24} color="#6366f1" />} 
                  color="#6366f1" 
                  onClick={() => onNavigate && onNavigate('tasks')}
                />
                <MetricCard 
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
                />
                <MetricCard 
                  title="Workspace Efficiency" 
                  value={`${data.overall_efficiency}%`} 
                  icon={<Target size={24} color="#f59e0b" />} 
                  color="#f59e0b" 
                  onClick={() => onNavigate && onNavigate('profile')}
                />
                <MetricCard 
                  title="Workspace Goals" 
                  value={data.total_goals} 
                  icon={<Target size={24} color="#10b981" />} 
                  color="#10b981" 
                  onClick={() => onNavigate && onNavigate('goals')}
                />
              </div>

              {/* Member Comparison Chart */}
              <div 
                onClick={() => onNavigate && onNavigate('tasks')}
                style={{ 
                  backgroundColor: '#fff', 
                  padding: '1.5rem', 
                  borderRadius: '16px', 
                  border: '1px solid #e2e8f0', 
                  boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                  cursor: 'pointer',
                  transition: 'transform 0.2s, box-shadow 0.2s'
                }}
                className="interactive-dashboard-card"
              >
                <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#0f172a', marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>Member-Wise Performance & Overdue Overview</span>
                  <span style={{ fontSize: '0.75rem', color: '#6366f1', fontWeight: 500 }}>Click to Drill Down Tasks</span>
                </h3>
                <div style={{ height: 350, width: '100%' }}>
                  {data.member_stats.length === 0 ? (
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
                  )}
                </div>
              </div>

              {/* Performance Leaderboard Grid */}
              <div 
                onClick={() => onNavigate && onNavigate('members')}
                style={{ 
                  backgroundColor: '#fff', 
                  padding: '1.5rem', 
                  borderRadius: '16px', 
                  border: '1px solid #e2e8f0', 
                  boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                  cursor: 'pointer',
                  transition: 'transform 0.2s, box-shadow 0.2s'
                }}
                className="interactive-dashboard-card"
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#0f172a', margin: 0, display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
                    <span>Workspace Leaderboard & Status</span>
                    <span style={{ fontSize: '0.75rem', color: '#6366f1', fontWeight: 500 }}>Click to Manage Team</span>
                  </h3>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {data.member_stats.length === 0 ? (
                    <div style={{ textAlign: 'center', color: '#64748b', fontSize: '0.85rem', padding: '1.5rem 0' }}>
                      No members matching these filter parameters.
                    </div>
                  ) : (
                    data.member_stats.map((member, idx) => (
                      <div key={member.user_id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', backgroundColor: '#f8fafc', borderRadius: '12px', border: '1px solid #f1f5f9' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          <div style={{ width: 32, height: 32, borderRadius: '50%', backgroundColor: idx === 0 ? '#fef3c7' : '#eef2ff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '0.85rem', color: idx === 0 ? '#d97706' : '#6366f1' }}>
                            {idx + 1}
                          </div>
                          <div>
                            <div style={{ fontWeight: 600, color: '#1e293b', fontSize: '0.9rem' }}>{member.name}</div>
                            <div style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'capitalize' }}>{member.role}</div>
                          </div>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
                          <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Tasks</div>
                            <div style={{ fontWeight: 600, color: '#0f172a', fontSize: '0.9rem' }}>{member.completed_tasks}/{member.total_tasks}</div>
                          </div>
                          <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Efficiency</div>
                            <div style={{ fontWeight: 700, color: '#10b981', fontSize: '0.95rem' }}>{member.efficiency}%</div>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </>
          )}

        </div>

      </div>
    </div>
  );
}

// Custom drop-down filter shell component
const DropdownFilter = ({ label, icon, isOpen, onClick, children, isActive, badgeCount }) => {
  return (
    <div style={{ position: 'relative' }}>
      <button
        onClick={onClick}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '8px 12px',
          fontSize: '0.82rem',
          fontWeight: 600,
          color: isActive ? '#4f46e5' : '#475569',
          backgroundColor: isActive ? '#eef2ff' : '#ffffff',
          border: isActive ? '1px solid #818cf8' : '1px solid #e2e8f0',
          borderRadius: '8px',
          cursor: 'pointer',
          transition: 'all 0.15s ease-in-out',
          height: '36px',
          outline: 'none',
          boxShadow: isActive ? '0 0 0 2px rgba(99, 102, 241, 0.1)' : '0 1px 2px rgba(0,0,0,0.03)',
        }}
        onMouseEnter={e => {
          if (!isActive) e.currentTarget.style.backgroundColor = '#f8fafc';
        }}
        onMouseLeave={e => {
          if (!isActive) e.currentTarget.style.backgroundColor = '#ffffff';
        }}
      >
        {icon}
        <span>{label}</span>
        {badgeCount > 0 && (
          <span style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minWidth: '16px',
            height: '16px',
            padding: '0 4px',
            fontSize: '0.65rem',
            fontWeight: 700,
            color: '#ffffff',
            backgroundColor: '#4f46e5',
            borderRadius: '99px',
          }}>
            {badgeCount}
          </span>
        )}
        <ChevronDown size={13} style={{ 
          transform: isOpen ? 'rotate(180deg)' : 'rotate(0)', 
          transition: 'transform 0.15s ease-in-out',
          color: isActive ? '#4f46e5' : '#94a3b8'
        }} />
      </button>

      {isOpen && (
        <div style={{
          position: 'absolute',
          top: '42px',
          left: 0,
          zIndex: 50,
          minWidth: '220px',
          maxHeight: '320px',
          overflowY: 'auto',
          backgroundColor: '#ffffff',
          border: '1px solid #e2e8f0',
          borderRadius: '8px',
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.03)',
          padding: '6px',
        }}>
          {children}
        </div>
      )}
    </div>
  );
};

// Reusable filter summary badge
const FilterBadge = ({ label, onRemove }) => (
  <span style={{
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
    backgroundColor: '#f1f5f9',
    color: '#334155',
    padding: '3px 8px',
    borderRadius: '6px',
    fontSize: '0.75rem',
    fontWeight: 500,
    border: '1px solid #e2e8f0'
  }}>
    {label}
    <X 
      size={12} 
      onClick={onRemove}
      style={{ cursor: 'pointer', color: '#64748b', borderRadius: '50%' }}
      onMouseEnter={e => e.currentTarget.style.color = '#ef4444'}
      onMouseLeave={e => e.currentTarget.style.color = '#64748b'}
    />
  </span>
);

// Helper for XCircle icon
const XCircle = ({ size }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"></circle>
    <line x1="15" y1="9" x2="9" y2="15"></line>
    <line x1="9" y1="9" x2="15" y2="15"></line>
  </svg>
);

// Reusable Metric Card matching core style with dynamic hover support
const MetricCard = ({ title, value, icon, color, onClick }) => (
  <div 
    onClick={onClick}
    style={{ 
      backgroundColor: '#fff', 
      padding: '1.5rem', 
      borderRadius: '16px', 
      border: '1px solid #e2e8f0', 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center',
      boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
      borderLeft: `4px solid ${color}`,
      cursor: onClick ? 'pointer' : 'default',
      transition: 'transform 0.2s, box-shadow 0.2s'
    }}
    className="interactive-metric-card"
  >
    <div>
      <span style={{ color: '#64748b', fontSize: '0.85rem', fontWeight: 500 }}>{title}</span>
      <h2 style={{ color: '#0f172a', fontSize: '1.8rem', fontWeight: 700, margin: '6px 0 0 0' }}>{value}</h2>
    </div>
    <div style={{ width: 48, height: 48, borderRadius: '12px', backgroundColor: `${color}10`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      {icon}
    </div>
  </div>
);
