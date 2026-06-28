import { useState, useEffect, useCallback } from 'react';
import { checkFreeMembers, updateOrgTask } from '../api';
import { Clock, Award, UserCheck, AlertCircle, CheckCircle, Inbox } from 'lucide-react';

export default function CheckFreeMembersModal({ isOpen, onClose, selectedOrg, handleLoadTasks }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [freeMembers, setFreeMembers] = useState([]);
  const [assigningId, setAssigningId] = useState(null);

  const fetchFreeMembers = useCallback(async () => {
    if (!selectedOrg) return;
    setLoading(true);
    setError(null);
    try {
      const data = await checkFreeMembers(selectedOrg.id);
      setFreeMembers(data.free_members || []);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.error || err.response?.data?.detail || "Failed to fetch recently freed members.");
    } finally {
      setLoading(false);
    }
  }, [selectedOrg]);

  useEffect(() => {
    if (!isOpen || !selectedOrg) return;
    let cancelled = false;

    (async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await checkFreeMembers(selectedOrg.id);
        if (cancelled) return;
        setFreeMembers(data.free_members || []);
        setSuccess(null);
      } catch (err) {
        if (cancelled) return;
        console.error(err);
        setError(err.response?.data?.error || err.response?.data?.detail || "Failed to fetch recently freed members.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => { cancelled = true; };
  }, [isOpen, selectedOrg]);

  if (!isOpen) return null;

  const handleAssign = async (taskId, memberId, memberName, taskTitle) => {
    setAssigningId(`${taskId}-${memberId}`);
    setError(null);
    setSuccess(null);
    try {
      await updateOrgTask(selectedOrg.slug, taskId, { assignees: [memberId] });
      setSuccess(`Assigned "${taskTitle}" to ${memberName} successfully!`);
      handleLoadTasks();
      // Refresh the free members lists to reflect the new assignment
      await fetchFreeMembers();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.error || err.response?.data?.detail || "Failed to assign task.");
    } finally {
      setAssigningId(null);
    }
  };

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(15, 23, 42, 0.4)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', backdropFilter: 'blur(4px)' }}>
      <div style={{ background: 'white', borderRadius: '16px', width: '700px', maxWidth: '95vw', height: '550px', display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.1)' }}>
        
        {/* Header */}
        <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#ffffff' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Clock size={20} style={{ color: '#6366f1' }} />
            <h3 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 600, color: '#0f172a' }}>
              Recently Freed Members <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 400 }}>(Last 15 Mins)</span>
            </h3>
          </div>
          <button onClick={onClose} style={{ border: 'none', background: 'none', cursor: 'pointer', color: '#94a3b8', fontSize: '1.5rem', padding: 0, lineHeight: 1, display: 'flex' }}>&times;</button>
        </div>

        {/* Content Area */}
        <div style={{ flex: 1, padding: '1.5rem', overflowY: 'auto', background: '#f8fafc', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          
          {/* Alerts */}
          {error && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#fef2f2', border: '1px solid #ef4444', color: '#b91c1c', padding: '0.75rem 1rem', borderRadius: '8px', fontSize: '0.85rem' }}>
              <AlertCircle size={16} />
              {error}
            </div>
          )}
          {success && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#ecfdf5', border: '1px solid #10b981', color: '#047857', padding: '0.75rem 1rem', borderRadius: '8px', fontSize: '0.85rem' }}>
              <CheckCircle size={16} />
              {success}
            </div>
          )}

          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', flex: 1, gap: '0.5rem' }}>
              <div style={{ border: '3px solid #f3f3f3', borderTop: '3px solid #6366f1', borderRadius: '50%', width: '30px', height: '30px', animation: 'spin 1s linear infinite' }} />
              <span style={{ fontSize: '0.85rem', color: '#64748b' }}>Checking workload changes...</span>
              <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
            </div>
          ) : freeMembers.length === 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', flex: 1, background: 'white', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '3rem 1.5rem', textAlign: 'center' }}>
              <Inbox size={40} style={{ color: '#cbd5e1', marginBottom: '0.75rem' }} />
              <span style={{ fontWeight: 600, color: '#1e293b', fontSize: '0.95rem' }}>No recently free members</span>
              <span style={{ color: '#64748b', fontSize: '0.82rem', marginTop: '0.25rem', maxWidth: '320px' }}>
                No workspace members finished a task in the last 15 minutes. Try checking again later.
              </span>
            </div>
          ) : (
            freeMembers.map(member => (
              <div key={member.member_id} style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem', boxShadow: '0 1px 3px rgba(0,0,0,0.02)' }}>
                {/* Member Title Row */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: '#e0e7ff', color: '#4f46e5', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.8rem', fontWeight: 600 }}>
                      {(member.name || member.email || 'U')[0].toUpperCase()}
                    </div>
                    <div>
                      <h4 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600, color: '#0f172a' }}>{member.name || member.email}</h4>
                      <p style={{ margin: 0, fontSize: '0.75rem', color: '#64748b' }}>{member.email}</p>

                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <span style={{ background: '#ecfdf5', color: '#047857', border: '1px solid #6ee7b7', fontSize: '0.65rem', padding: '0.15rem 0.45rem', borderRadius: '6px', fontWeight: 600 }}>
                      COMPLETED TASK
                    </span>
                    <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.78rem', color: '#1e293b', fontWeight: 500 }} title={member.finished_task_title}>
                      {member.finished_task_title && member.finished_task_title.length > 30 ? `${member.finished_task_title.substring(0, 30)}...` : (member.finished_task_title || 'Task')}
                    </p>
                  </div>
                </div>

                {/* Recommendations Header */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <span style={{ fontSize: '0.75rem', color: '#475569', fontWeight: 700, letterSpacing: '0.03em', textTransform: 'uppercase' }}>
                    Recommended Tasks
                  </span>
                  
                  {member.suggestions.length === 0 ? (
                    <p style={{ margin: 0, fontSize: '0.8rem', color: '#94a3b8', fontStyle: 'italic' }}>
                      No unassigned tasks found matching this member's skillset.
                    </p>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      {member.suggestions.map(sugg => (
                        <div key={sugg.task_id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem 1rem', background: '#f8fafc', border: '1px solid #f1f5f9', borderRadius: '8px', gap: '1rem' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', flex: 1 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
                              <span style={{ fontSize: '0.65rem', padding: '0.1rem 0.35rem', background: sugg.task_priority === 'high' ? '#fee2e2' : sugg.task_priority === 'medium' ? '#ffedd5' : '#f1f5f9', color: sugg.task_priority === 'high' ? '#b91c1c' : sugg.task_priority === 'medium' ? '#c2410c' : '#475569', borderRadius: '4px', textTransform: 'uppercase', fontWeight: 600 }}>
                                {sugg.task_priority}
                              </span>
                              <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#1e293b' }}>
                                {sugg.task_title}
                              </span>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.72rem', color: '#64748b' }}>
                              <Award size={12} style={{ color: '#fbbf24' }} /> Match Score: <strong>{sugg.match_score}</strong>
                              <span style={{ color: '#cbd5e1' }}>|</span>
                              <span style={{ fontStyle: 'italic' }}>{sugg.reason}</span>
                            </div>
                          </div>

                          <button
                            type="button"
                            className="btn-primary"
                            disabled={assigningId === `${sugg.task_id}-${member.member_id}`}
                            onClick={() => handleAssign(sugg.task_id, member.member_id, member.name || member.email, sugg.task_title)}
                            style={{ 
                              padding: '0.4rem 0.8rem', 
                              fontSize: '0.75rem', 
                              borderRadius: '6px', 
                              width: 'auto',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '0.25rem',
                              background: '#6366f1',
                              borderColor: 'transparent',
                              whiteSpace: 'nowrap'
                            }}
                          >
                            <UserCheck size={12} />
                            {assigningId === `${sugg.task_id}-${member.member_id}` ? 'Assigning...' : 'Assign Now'}
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}

        </div>
        
        {/* Footer */}
        <div style={{ padding: '1rem 1.5rem', borderTop: '1px solid #e2e8f0', display: 'flex', justifyContent: 'flex-end', background: '#ffffff' }}>
          <button onClick={onClose} className="btn-secondary" style={{ width: 'auto', padding: '0.5rem 1.2rem', fontSize: '0.85rem', borderRadius: '8px' }}>
            Close
          </button>
        </div>

      </div>
    </div>
  );
}
