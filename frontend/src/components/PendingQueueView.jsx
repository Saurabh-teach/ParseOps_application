import { useState } from 'react';
// Commented: Smart Suggestion Feature
import { 
  // assignSuggestedTask, 
  changeAssigneeOverride, 
  deleteOrgTask,
  manualScheduleTasks,
  // bulkScheduleTasks,
  // previewScheduleTasks,
  // applyScheduleTasks
} from '../api';
import { 
  Play, 
  AlertCircle, 
  CheckCircle, 
  Inbox,
  Edit3,
  Trash2
} from 'lucide-react';

const priorityWeight = {
  high: 3,
  medium: 2,
  low: 1
};

export default function PendingQueueView({ 
  selectedOrg, 
  tasks, 
  handleLoadTasks, 
  orgMembers, 
  goals,
  onEditTask
}) {
  const [assigningId, setAssigningId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [selectedMembers, setSelectedMembers] = useState({});

  const role = selectedOrg?.my_status?.role;
  const customPerms = selectedOrg?.my_status?.custom_permissions || {};
  const isManagement = role === 'owner' || role === 'admin';
  const canDeleteTasks = isManagement || customPerms.delete_workspace_tasks === true;

  const [scheduling, setScheduling] = useState(false);

  const handleRunSchedulerNow = async () => {
    if (!selectedOrg?.id) return;
    setScheduling(true);
    setSuccessMsg(null);
    setErrorMsg(null);
    try {
      await manualScheduleTasks(selectedOrg.id);
      setSuccessMsg('Scheduler executed successfully! Reloading...');
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    } catch (err) {
      console.error(err);
      const errMsg = err.response?.data?.error || err.response?.data?.detail || 'Failed to run scheduler.';
      setErrorMsg(errMsg);
      setTimeout(() => setErrorMsg(null), 5000);
    } finally {
      setScheduling(false);
    }
  };

  // Filter tasks that are queued (either unassigned, or assigned but no time slot)
  const pendingTasks = (Array.isArray(tasks) ? tasks : []).filter(
    t => t.schedule_status === 'QUEUED' && t.status !== 'done' && !t.is_deleted
  );

  // Sort by priority weight descending (Urgent/High first)
  const sortedTasks = [...pendingTasks].sort((a, b) => {
    const wA = priorityWeight[a.priority] || 0;
    const wB = priorityWeight[b.priority] || 0;
    return wB - wA;
  });



  const handleChangeAssignee = async (taskId, employeeId) => {
    if (!employeeId) return;
    setAssigningId(taskId);
    setSuccessMsg(null);
    setErrorMsg(null);
    try {
      await changeAssigneeOverride(taskId, employeeId);
      setSuccessMsg(`Successfully reassigned task.`);
      handleLoadTasks();
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err) {
      console.error(err);
      const errMsg = err.response?.data?.error || err.response?.data?.detail || "Failed to reassign task.";
      setErrorMsg(errMsg);
      setTimeout(() => setErrorMsg(null), 5000);
    } finally {
      setAssigningId(null);
    }
  };

  const handleDeleteTask = async (taskId) => {
    if (!selectedOrg?.slug || !window.confirm('Are you sure you want to delete this task?')) return;

    setDeletingId(taskId);
    setSuccessMsg(null);
    setErrorMsg(null);
    try {
      await deleteOrgTask(selectedOrg.slug, taskId);
      setSelectedMembers(prev => {
        const next = { ...prev };
        delete next[taskId];
        return next;
      });
      setSuccessMsg('Task deleted from queue.');
      handleLoadTasks();
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err) {
      console.error(err);
      const errMsg = err.response?.data?.error || err.response?.data?.detail || 'Failed to delete task or access denied.';
      setErrorMsg(errMsg);
      setTimeout(() => setErrorMsg(null), 5000);
    } finally {
      setDeletingId(null);
    }
  };





  return (
    <div className="pending-queue-view" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', height: '100%', padding: '1rem' }}>
      
      {/* Header Info */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          <h2 className="section-header" style={{ margin: 0, fontSize: '1.4rem', color: '#1e293b' }}>Pending & Unassigned Tasks</h2>
          {/* <p className="section-desc" style={{ margin: 0, color: '#64748b', fontSize: '0.88rem' }}>
            Assign pending workspace tasks to the best-suited team members using smart suitability matches and fatigue balances.
          </p> */}
        </div>
        {isManagement && (
          <button
            type="button"
            onClick={handleRunSchedulerNow}
            disabled={scheduling}
            style={{
              padding: '0.6rem 1.25rem',
              fontSize: '0.88rem',
              borderRadius: '8px',
              background: scheduling ? '#cbd5e1' : '#6366f1',
              color: scheduling ? '#94a3b8' : 'white',
              border: 'none',
              fontWeight: 600,
              cursor: scheduling ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              transition: 'all 0.2s',
              boxShadow: scheduling ? 'none' : '0 4px 6px -1px rgba(99, 102, 241, 0.2), 0 2px 4px -1px rgba(99, 102, 241, 0.1)'
            }}
            onMouseEnter={e => {
              if (!e.currentTarget.disabled) {
                e.currentTarget.style.background = '#4f46e5';
              }
            }}
            onMouseLeave={e => {
              if (!e.currentTarget.disabled) {
                e.currentTarget.style.background = '#6366f1';
              }
            }}
          >
            <Play size={16} fill={scheduling ? '#94a3b8' : 'white'} />
            {scheduling ? 'Scheduling...' : 'Run Scheduler Now'}
          </button>
        )}

      </div>


      {/* Notifications */}
      {successMsg && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#ecfdf5', border: '1px solid #10b981', color: '#047857', padding: '0.75rem 1rem', borderRadius: '8px', fontSize: '0.85rem', fontWeight: 500 }}>
          <CheckCircle size={16} />
          {successMsg}
        </div>
      )}
      {errorMsg && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#fef2f2', border: '1px solid #ef4444', color: '#b91c1c', padding: '0.75rem 1rem', borderRadius: '8px', fontSize: '0.85rem', fontWeight: 500 }}>
          <AlertCircle size={16} />
          {errorMsg}
        </div>
      )}

      {/* Main Container */}
      {sortedTasks.length === 0 ? (
          <div className="premium-card-settings" style={{ padding: '4rem 2rem', textAlign: 'center', background: 'white', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
            <Inbox size={48} style={{ color: '#cbd5e1', marginBottom: '1rem' }} />
            <p style={{ fontSize: '1.1rem', fontWeight: 600, color: '#1e293b', marginBottom: '0.25rem' }}>No pending tasks in queue</p>
            <p style={{ fontSize: '0.85rem', color: '#64748b' }}>All tasks have been successfully assigned to your workspace members.</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1rem' }}>
            {sortedTasks.map(task => {
              const goalObj = (goals || []).find(g => g.id === task.goal);

              return (
                <div 
                  key={task.id} 
                  style={{ 
                    background: 'white', 
                    borderRadius: '12px', 
                    border: '1px solid #e2e8f0', 
                    padding: '1.25rem', 
                    boxShadow: '0 1px 3px rgba(0,0,0,0.02)',
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center', 
                    gap: '1.5rem',
                    flexWrap: 'wrap',
                    transition: 'transform 0.2s, box-shadow 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.05)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'none';
                    e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.02)';
                  }}
                >
                  {/* Left side: Task Details */}
                  <div style={{ flex: '1 1 300px', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                      <span 
                        className={`member-role-badge-premium role-${task.priority === 'high' ? 'high' : task.priority === 'medium' ? 'medium' : 'low'}`} 
                        style={{ fontSize: '0.65rem', textTransform: 'uppercase', padding: '0.15rem 0.45rem' }}
                      >
                        {task.priority.toUpperCase()}
                      </span>
                      <h3 
                        onClick={() => onEditTask && onEditTask(task)}
                        style={{ 
                          margin: 0, 
                          fontSize: '1rem', 
                          fontWeight: 600, 
                          color: '#0f172a',
                          cursor: 'pointer',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.25rem'
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.textDecoration = 'underline'}
                        onMouseLeave={(e) => e.currentTarget.style.textDecoration = 'none'}
                      >
                        {task.title}
                        <Edit3 size={13} style={{ color: '#6366f1', marginLeft: '0.25rem' }} />
                      </h3>
                      {goalObj && (
                        <span className="member-role-badge-premium role-medium" style={{ textTransform: 'none', fontSize: '0.6rem', padding: '0.1rem 0.35rem', background: '#e0f2fe', color: '#0369a1', borderColor: '#bae6fd' }}>
                          🎯 {goalObj.title}
                        </span>
                      )}
                    </div>

                    {task.description && (
                      <p style={{ margin: 0, fontSize: '0.82rem', color: '#64748b', lineHeight: '1.4' }}>{task.description}</p>
                    )}

                    <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.2rem' }}>
                      <span>Estimated: <strong>{task.estimated_hours || (task.estimated_minutes ? (task.estimated_minutes/60).toFixed(1) : '1.0')}h</strong></span>
                      {task.due_date && (
                        <span>Due: <strong>{new Date(task.due_date).toLocaleDateString()}</strong></span>
                      )}
                    </div>
                  </div>

                  {/* Right side: Manual Assign (Commented out Smart Suggestion) */}
                  <div 
                    style={{ 
                      flex: '1 1 250px',
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'space-between', 
                      gap: '1rem',
                      background: '#f8fafc', 
                      padding: '0.85rem 1.1rem', 
                      borderRadius: '10px', 
                      border: '1px solid #f1f5f9' 
                    }}
                  >

                    {/* Keep manual assignment active */}
                    {(isManagement || canDeleteTasks) && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', width: '100%' }}>
                        {isManagement && (
                          <>
                            <select
                              value={selectedMembers[task.id] || task.assignee || ''}
                              onChange={e => setSelectedMembers(prev => ({ ...prev, [task.id]: e.target.value }))}
                              style={{
                                padding: '0.35rem 0.5rem',
                                borderRadius: '6px',
                                border: '1px solid #cbd5e1',
                                background: 'white',
                                fontSize: '0.78rem',
                                width: '100%',
                                color: '#1e293b'
                              }}
                            >
                              <option value='' disabled>Select member</option>
                              {(orgMembers || []).map(m => {
                                const namePart = m.user?.first_name || m.user?.last_name
                                  ? `${m.user.first_name || ''} ${m.user.last_name || ''}`.trim()
                                  : '';
                                const emailPart = m.user?.email || m.email || '';
                                const displayName = namePart ? `${namePart} (${emailPart})` : emailPart;
                                
                                return (
                                  <option key={m.user?.id || m.user_id} value={m.user?.id || m.user_id}>
                                    {displayName}
                                  </option>
                                );
                              })}
                            </select>
                            <button
                              type="button"
                              className="btn-primary"
                              disabled={!(selectedMembers[task.id] || task.assignee) || assigningId === task.id}
                              onClick={() => handleChangeAssignee(task.id, selectedMembers[task.id] || task.assignee)}
                              style={{
                                padding: '0.35rem 0.75rem',
                                fontSize: '0.76rem',
                                borderRadius: '6px',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.35rem',
                                background: (!(selectedMembers[task.id] || task.assignee) || assigningId === task.id) ? '#cbd5e1' : '#6366f1',
                                borderColor: 'transparent',
                                color: (!(selectedMembers[task.id] || task.assignee) || assigningId === task.id) ? '#94a3b8' : 'white',
                                cursor: (!(selectedMembers[task.id] || task.assignee) || assigningId === task.id) ? 'not-allowed' : 'pointer',
                                whiteSpace: 'nowrap'
                              }}
                            >
                              {task.assignee && (!selectedMembers[task.id] || selectedMembers[task.id] === task.assignee) ? 'Confirm' : (task.assignee ? 'Change' : 'Assign')}
                            </button>
                          </>
                        )}
                        {canDeleteTasks && (
                          <button
                            type="button"
                            className="danger-btn-premium"
                            title="Delete task"
                            aria-label={`Delete ${task.title}`}
                            disabled={deletingId === task.id || assigningId === task.id}
                            onClick={() => handleDeleteTask(task.id)}
                            style={{
                              width: '34px',
                              minWidth: '34px',
                              height: '34px',
                              padding: 0,
                              borderRadius: '6px',
                              display: 'inline-flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              cursor: (deletingId === task.id || assigningId === task.id) ? 'not-allowed' : 'pointer',
                              opacity: (deletingId === task.id || assigningId === task.id) ? 0.65 : 1
                            }}
                          >
                            <Trash2 size={14} />
                          </button>
                        )}
                      </div>
                    )}
                  </div>

                </div>
              );
            })}
          </div>
        )
      }

    </div>
  );
}
