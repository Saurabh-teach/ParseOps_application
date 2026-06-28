import { useState } from 'react';
import api from '../api';
import { X, CheckCircle2, AlertCircle, AlertTriangle } from 'lucide-react';

const TaskFeedbackModal = ({ isOpen, onClose, taskId, taskTitle }) => {
  const [difficulty, setDifficulty] = useState('');
  const [comments, setComments] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!difficulty) {
      setError('Please select a difficulty level');
      return;
    }
    setError('');
    setIsSubmitting(true);

    try {
      await api.post(
        `/tasks/${taskId}/feedback/`,
        { difficulty, comments }
      );
      setSuccess(true);
      setTimeout(() => {
        onClose();
        setSuccess(false);
        setDifficulty('');
        setComments('');
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit feedback');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      backgroundColor: 'rgba(15, 23, 42, 0.6)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
    }}>
      <div style={{
        backgroundColor: '#fff',
        borderRadius: '16px',
        width: '100%',
        maxWidth: '500px',
        padding: '2rem',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        position: 'relative'
      }}>
        <button 
          onClick={onClose}
          style={{ position: 'absolute', top: '1.5rem', right: '1.5rem', background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}
        >
          <X size={20} />
        </button>

        {success ? (
          <div style={{ textAlign: 'center', padding: '2rem 0' }}>
            <CheckCircle2 size={48} color="#10b981" style={{ margin: '0 auto 1rem' }} />
            <h3 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#0f172a', marginBottom: '0.5rem' }}>Feedback Submitted!</h3>
            <p style={{ color: '#64748b' }}>Thank you for helping the team improve.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.5rem' }}>Task Completed! 🎉</h2>
              <p style={{ color: '#64748b', fontSize: '0.9rem' }}>How was working on <strong>{taskTitle}</strong>?</p>
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '1rem' }}>
                Difficulty Level *
              </label>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <button
                  type="button"
                  onClick={() => setDifficulty('easy')}
                  style={{
                    flex: 1,
                    padding: '1rem',
                    borderRadius: '12px',
                    border: `2px solid ${difficulty === 'easy' ? '#10b981' : '#e2e8f0'}`,
                    backgroundColor: difficulty === 'easy' ? '#ecfdf5' : '#fff',
                    color: difficulty === 'easy' ? '#065f46' : '#64748b',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '0.5rem',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                >
                  <CheckCircle2 size={24} color={difficulty === 'easy' ? '#10b981' : '#cbd5e1'} />
                  <span style={{ fontWeight: 600 }}>Easy</span>
                </button>
                <button
                  type="button"
                  onClick={() => setDifficulty('medium')}
                  style={{
                    flex: 1,
                    padding: '1rem',
                    borderRadius: '12px',
                    border: `2px solid ${difficulty === 'medium' ? '#f59e0b' : '#e2e8f0'}`,
                    backgroundColor: difficulty === 'medium' ? '#fffbeb' : '#fff',
                    color: difficulty === 'medium' ? '#92400e' : '#64748b',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '0.5rem',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                >
                  <AlertTriangle size={24} color={difficulty === 'medium' ? '#f59e0b' : '#cbd5e1'} />
                  <span style={{ fontWeight: 600 }}>Medium</span>
                </button>
                <button
                  type="button"
                  onClick={() => setDifficulty('hard')}
                  style={{
                    flex: 1,
                    padding: '1rem',
                    borderRadius: '12px',
                    border: `2px solid ${difficulty === 'hard' ? '#ef4444' : '#e2e8f0'}`,
                    backgroundColor: difficulty === 'hard' ? '#fef2f2' : '#fff',
                    color: difficulty === 'hard' ? '#991b1b' : '#64748b',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '0.5rem',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                >
                  <AlertCircle size={24} color={difficulty === 'hard' ? '#ef4444' : '#cbd5e1'} />
                  <span style={{ fontWeight: 600 }}>Hard</span>
                </button>
              </div>
            </div>

            <div style={{ marginBottom: '2rem' }}>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#334155', marginBottom: '0.5rem' }}>
                Comments (Optional)
              </label>
              <textarea
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                placeholder="What problems did you face? What helped you complete it?"
                style={{
                  width: '100%',
                  padding: '0.75rem 1rem',
                  borderRadius: '8px',
                  border: '1px solid #e2e8f0',
                  fontSize: '0.875rem',
                  minHeight: '100px',
                  resize: 'vertical',
                  fontFamily: 'inherit'
                }}
              />
            </div>

            {error && <div style={{ color: '#ef4444', fontSize: '0.875rem', marginBottom: '1rem', textAlign: 'center' }}>{error}</div>}

            <div style={{ display: 'flex', gap: '1rem' }}>
              <button
                type="button"
                onClick={onClose}
                style={{
                  flex: 1,
                  padding: '0.75rem',
                  backgroundColor: '#f1f5f9',
                  color: '#475569',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                Skip
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                style={{
                  flex: 1,
                  padding: '0.75rem',
                  backgroundColor: '#6366f1',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: 600,
                  cursor: isSubmitting ? 'not-allowed' : 'pointer',
                  opacity: isSubmitting ? 0.7 : 1
                }}
              >
                {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default TaskFeedbackModal;
