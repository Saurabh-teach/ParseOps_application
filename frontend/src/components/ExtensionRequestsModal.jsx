import { useState, useEffect, useCallback } from 'react';
import { X, Check, Calendar } from 'lucide-react';
import { getExtensionRequests, reviewExtensionRequest } from '../api';

const ExtensionRequestsModal = ({ isOpen, onClose, orgId }) => {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Review form state
  const [activeReviewId, setActiveReviewId] = useState(null);
  const [managerComment, setManagerComment] = useState('');
  const [status, setStatus] = useState('approved');
  const [proposedDate, setProposedDate] = useState('');
  const [reviewing, setReviewing] = useState(false);

  const loadRequests = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getExtensionRequests(orgId);
      setRequests(data.results || data);
      setError(null);
    } catch {
      setError('Failed to load extension requests.');
    } finally {
      setLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    if (!isOpen || !orgId) return;
    let cancelled = false;

    (async () => {
      try {
        setLoading(true);
        const response = await getExtensionRequests(orgId);
        if (cancelled) return;
        setRequests(response.results || response);
        setError(null);
      } catch {
        if (cancelled) return;
        setError('Failed to load extension requests.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => { cancelled = true; };
  }, [isOpen, orgId]);

  const handleReviewSubmit = async (e, requestId) => {
    e.preventDefault();
    setReviewing(true);
    try {
      const payload = { status, manager_comment: managerComment };
      if (status === 'modified') {
        if (!proposedDate) {
          alert("Please provide a new date for modified requests.");
          setReviewing(false);
          return;
        }
        payload.proposed_date = new Date(proposedDate).toISOString();
      }

      await reviewExtensionRequest(requestId, payload);
      setActiveReviewId(null);
      setManagerComment('');
      setStatus('approved');
      setProposedDate('');
      await loadRequests();
    } catch {
      alert("Failed to submit review.");
    } finally {
      setReviewing(false);
    }
  };

  if (!isOpen) return null;

  const pendingRequests = requests.filter(r => r.status === 'pending');
  const historyRequests = requests.filter(r => r.status !== 'pending');

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
      backgroundColor: 'rgba(15, 23, 42, 0.75)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999,
    }}>
      <div style={{
        backgroundColor: '#f8fafc', borderRadius: '16px', width: '100%', maxWidth: '800px', height: '80vh',
        position: 'relative', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)', display: 'flex', flexDirection: 'column'
      }}>
        <div style={{ padding: '1.5rem 2rem', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#fff', borderRadius: '16px 16px 0 0' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a', margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Calendar size={24} color="#6366f1" /> Extension Requests
          </h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}>
            <X size={24} />
          </button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '2rem' }}>
          {loading ? (
            <div style={{ textAlign: 'center', color: '#64748b' }}>Loading requests...</div>
          ) : error ? (
            <div style={{ color: '#ef4444', textAlign: 'center' }}>{error}</div>
          ) : (
            <>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#334155', marginBottom: '1rem' }}>Pending ({pendingRequests.length})</h3>
              {pendingRequests.length === 0 ? (
                <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '2rem' }}>No pending requests.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}>
                  {pendingRequests.map(req => (
                    <div key={req.id} style={{ backgroundColor: '#fff', borderRadius: '12px', padding: '1.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', borderLeft: '4px solid #f59e0b' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                        <div>
                          <strong style={{ fontSize: '1rem', color: '#0f172a' }}>Task: {req.task_title || req.task}</strong>
                          <div style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '0.25rem' }}>Requested by: {req.requested_by_email || 'User'}</div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <span style={{ fontSize: '0.75rem', padding: '0.2rem 0.6rem', borderRadius: '12px', backgroundColor: '#fef3c7', color: '#d97706', fontWeight: 600 }}>{req.reason_type.replace('_', ' ').toUpperCase()}</span>
                        </div>
                      </div>
                      
                      <div style={{ backgroundColor: '#f8fafc', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>
                        <div style={{ display: 'flex', gap: '2rem', fontSize: '0.875rem' }}>
                          <div>
                            <span style={{ color: '#64748b' }}>Current Due Date:</span>
                            <div style={{ fontWeight: 600, color: '#0f172a', marginTop: '0.25rem' }}>{req.current_due_date ? new Date(req.current_due_date).toLocaleDateString() : 'None'}</div>
                          </div>
                          <div>
                            <span style={{ color: '#64748b' }}>Proposed Due Date:</span>
                            <div style={{ fontWeight: 600, color: '#4f46e5', marginTop: '0.25rem' }}>{new Date(req.proposed_date).toLocaleDateString()}</div>
                          </div>
                        </div>
                        {req.reason_text && (
                          <div style={{ marginTop: '1rem', fontSize: '0.875rem', color: '#475569', fontStyle: 'italic' }}>
                            "{req.reason_text}"
                          </div>
                        )}
                      </div>

                      {activeReviewId === req.id ? (
                        <form onSubmit={(e) => handleReviewSubmit(e, req.id)} style={{ borderTop: '1px solid #e2e8f0', paddingTop: '1rem' }}>
                          <div style={{ marginBottom: '1rem' }}>
                            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#334155', marginBottom: '0.5rem' }}>Decision</label>
                            <div style={{ display: 'flex', gap: '1rem' }}>
                              <label style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.875rem', cursor: 'pointer' }}>
                                <input type="radio" name="status" checked={status === 'approved'} onChange={() => setStatus('approved')} />
                                <span style={{ color: '#10b981', fontWeight: 600 }}>Approve</span>
                              </label>
                              <label style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.875rem', cursor: 'pointer' }}>
                                <input type="radio" name="status" checked={status === 'rejected'} onChange={() => setStatus('rejected')} />
                                <span style={{ color: '#ef4444', fontWeight: 600 }}>Reject</span>
                              </label>
                              <label style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.875rem', cursor: 'pointer' }}>
                                <input type="radio" name="status" checked={status === 'modified'} onChange={() => { setStatus('modified'); setProposedDate(req.proposed_date.split('T')[0] + 'T12:00'); }} />
                                <span style={{ color: '#f59e0b', fontWeight: 600 }}>Modify Date</span>
                              </label>
                            </div>
                          </div>

                          {status === 'modified' && (
                            <div style={{ marginBottom: '1rem' }}>
                              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#334155', marginBottom: '0.5rem' }}>New Date</label>
                              <input type="datetime-local" value={proposedDate} onChange={e => setProposedDate(e.target.value)} style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1' }} required />
                            </div>
                          )}

                          <div style={{ marginBottom: '1rem' }}>
                            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#334155', marginBottom: '0.5rem' }}>Feedback / Comment (Optional)</label>
                            <input type="text" value={managerComment} onChange={e => setManagerComment(e.target.value)} placeholder="Explain your decision..." style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.875rem' }} />
                          </div>

                          <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                            <button type="button" onClick={() => setActiveReviewId(null)} style={{ padding: '0.5rem 1rem', background: '#f1f5f9', border: 'none', borderRadius: '6px', color: '#475569', fontWeight: 600, cursor: 'pointer' }}>Cancel</button>
                            <button type="submit" disabled={reviewing} style={{ padding: '0.5rem 1rem', background: '#6366f1', border: 'none', borderRadius: '6px', color: '#fff', fontWeight: 600, cursor: 'pointer' }}>{reviewing ? 'Saving...' : 'Confirm'}</button>
                          </div>
                        </form>
                      ) : (
                        <button onClick={() => { setActiveReviewId(req.id); setStatus('approved'); setManagerComment(''); }} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 1rem', background: '#4f46e5', color: 'white', border: 'none', borderRadius: '6px', fontWeight: 600, cursor: 'pointer', fontSize: '0.875rem' }}>
                          <Check size={16} /> Review Request
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}

              <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#334155', marginBottom: '1rem', marginTop: '2rem' }}>History ({historyRequests.length})</h3>
              {historyRequests.length === 0 ? (
                <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>No past requests.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {historyRequests.map(req => (
                    <div key={req.id} style={{ backgroundColor: '#fff', borderRadius: '12px', padding: '1.25rem', border: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <strong style={{ fontSize: '0.95rem', color: '#0f172a' }}>Task: {req.task_title || req.task}</strong>
                        <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.25rem' }}>Requested by: {req.requested_by_email || 'User'}</div>
                        {req.manager_comment && <div style={{ fontSize: '0.8rem', color: '#475569', fontStyle: 'italic', marginTop: '0.5rem' }}>Manager: "{req.manager_comment}"</div>}
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <span style={{ 
                          fontSize: '0.75rem', padding: '0.3rem 0.6rem', borderRadius: '12px', fontWeight: 600,
                          backgroundColor: req.status === 'approved' ? '#dcfce7' : req.status === 'rejected' ? '#fee2e2' : '#fef3c7',
                          color: req.status === 'approved' ? '#166534' : req.status === 'rejected' ? '#991b1b' : '#d97706'
                        }}>
                          {req.status.toUpperCase()}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ExtensionRequestsModal;
