import { useState } from 'react';
import api from '../api';
import { X, Calendar, Clock, AlertCircle } from 'lucide-react';

const TaskExtensionModal = ({ isOpen, onClose, taskId, taskTitle, currentDueDate }) => {
  const [reasonType, setReasonType] = useState('more_time');
  const [reasonText, setReasonText] = useState('');
  const [proposedDate, setProposedDate] = useState('');
  const [requestedHours, setRequestedHours] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  console.log("TaskExtensionModal render, isOpen:", isOpen, "taskId:", taskId);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!proposedDate) {
      setError('Please select a proposed new due date.');
      return;
    }
    
    // Ensure proposed date is after current due date (basic check)
    if (currentDueDate && new Date(proposedDate) <= new Date(currentDueDate)) {
      setError('Proposed date must be later than the current due date.');
      return;
    }

    setError('');
    setIsSubmitting(true);

    try {

      await api.post(
        `/tasks/${taskId}/extension-request/`,
        {
          reason_type: reasonType,
          reason_text: reasonText,
          proposed_date: new Date(proposedDate).toISOString(),
          requested_hours: requestedHours ? parseFloat(requestedHours) : null
        }
      );
      
      setSuccess(true);
      setTimeout(() => {
        onClose();
        setSuccess(false);
        setReasonType('more_time');
        setReasonText('');
        setProposedDate('');
        setRequestedHours('');
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit extension request. You may already have a pending request.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
      backgroundColor: 'rgba(15, 23, 42, 0.75)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999,
    }}>
      <div style={{
        backgroundColor: '#fff', borderRadius: '16px', width: '100%', maxWidth: '500px',
        padding: '2rem', position: 'relative', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)'
      }}>
        <button onClick={onClose} style={{ position: 'absolute', top: '1.5rem', right: '1.5rem', background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}>
          <X size={20} />
        </button>

        {success ? (
          <div style={{ textAlign: 'center', padding: '2rem 0' }}>
            <Clock size={48} color="#6366f1" style={{ margin: '0 auto 1rem' }} />
            <h3 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#0f172a', marginBottom: '0.5rem' }}>Request Sent!</h3>
            <p style={{ color: '#64748b' }}>Your manager has been notified and will review your proposed date.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: '1.5rem' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Calendar size={24} color="#6366f1" /> Request Extension
              </h2>
              <p style={{ color: '#64748b', fontSize: '0.9rem' }}>Task: <strong>{taskTitle}</strong></p>
            </div>

            {error && (
              <div style={{ backgroundColor: '#fef2f2', borderLeft: '4px solid #ef4444', padding: '1rem', marginBottom: '1.5rem', borderRadius: '4px', display: 'flex', gap: '0.5rem', color: '#991b1b', fontSize: '0.875rem' }}>
                <AlertCircle size={16} /> {error}
              </div>
            )}

            <div style={{ marginBottom: '1.25rem' }}>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.5rem' }}>Reason for Delay *</label>
              <select 
                value={reasonType} 
                onChange={(e) => setReasonType(e.target.value)}
                style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '0.875rem', outline: 'none' }}
              >
                <option value="more_time">Need More Time</option>
                <option value="blocked">Blocked by Dependency</option>
                <option value="scope_change">Scope Change</option>
                <option value="personal">Personal / Sick Leave</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div style={{ marginBottom: '1.25rem' }}>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.5rem' }}>Proposed New Due Date *</label>
              <input 
                type="datetime-local" 
                value={proposedDate}
                onChange={(e) => setProposedDate(e.target.value)}
                style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '0.875rem', outline: 'none' }}
              />
            </div>

            <div style={{ marginBottom: '1.25rem' }}>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.5rem' }}>Extra Hours Requested (Optional)</label>
              <input 
                type="number" 
                step="0.5"
                min="0"
                placeholder="e.g. 2.0"
                value={requestedHours}
                onChange={(e) => setRequestedHours(e.target.value)}
                style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '0.875rem', outline: 'none' }}
              />
            </div>

            <div style={{ marginBottom: '2rem' }}>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.5rem' }}>Additional Details (Optional)</label>
              <textarea 
                value={reasonText}
                onChange={(e) => setReasonText(e.target.value)}
                placeholder="Explain why you need an extension..."
                style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '0.875rem', outline: 'none', minHeight: '80px', resize: 'vertical', fontFamily: 'inherit' }}
              />
            </div>

            <div style={{ display: 'flex', gap: '1rem' }}>
              <button type="button" onClick={onClose} style={{ flex: 1, padding: '0.75rem', backgroundColor: '#f1f5f9', color: '#475569', border: 'none', borderRadius: '8px', fontWeight: 600, cursor: 'pointer' }}>
                Cancel
              </button>
              <button type="submit" disabled={isSubmitting} style={{ flex: 2, padding: '0.75rem', backgroundColor: '#6366f1', color: '#fff', border: 'none', borderRadius: '8px', fontWeight: 600, cursor: isSubmitting ? 'not-allowed' : 'pointer', opacity: isSubmitting ? 0.7 : 1 }}>
                {isSubmitting ? 'Sending Request...' : 'Submit Request'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default TaskExtensionModal;
