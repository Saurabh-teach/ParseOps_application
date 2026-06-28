import re

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

target = "  updateTaskTicketStatus,"
replacement = "  updateTaskTicketStatus,\n  submitTaskProof,"

content = content.replace(target, replacement)

target_state = "  const [feedbackModalConfig, setFeedbackModalConfig] = useState({ isOpen: false, taskId: null, taskTitle: '' });"
replacement_state = """  const [feedbackModalConfig, setFeedbackModalConfig] = useState({ isOpen: false, taskId: null, taskTitle: '' });
  const [submissionModalConfig, setSubmissionModalConfig] = useState({ isOpen: false, ticketId: null, taskId: null, taskTitle: '' });
  const [submissionForm, setSubmissionForm] = useState({ comments: '', url_links: '', visibility: 'all', visible_to: [] });
  const [submissionFile, setSubmissionFile] = useState(null);"""

content = content.replace(target_state, replacement_state)

target_modal = """      {feedbackModalConfig.isOpen && (
        <TaskFeedbackModal
          taskId={feedbackModalConfig.taskId}"""

replacement_modal = """      {submissionModalConfig.isOpen && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 10000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ background: 'white', padding: '2rem', borderRadius: '12px', width: '90%', maxWidth: '500px', maxHeight: '90vh', overflowY: 'auto' }}>
            <h3 style={{ marginTop: 0, marginBottom: '1rem', fontSize: '1.25rem', color: '#0f172a' }}>Submit Task Proof</h3>
            <p style={{ fontSize: '0.85rem', color: '#475569', marginBottom: '1.5rem' }}>Please provide proof of work to mark "{submissionModalConfig.taskTitle}" as Done.</p>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="input-group">
                <label className="input-label">Comments / Description</label>
                <textarea 
                  className="input-field" 
                  rows="3" 
                  placeholder="What did you complete?"
                  value={submissionForm.comments}
                  onChange={(e) => setSubmissionForm({...submissionForm, comments: e.target.value})}
                  required
                />
              </div>
              
              <div className="input-group">
                <label className="input-label">Proof Links (URLs)</label>
                <textarea 
                  className="input-field" 
                  rows="2" 
                  placeholder="GitHub PR, Figma link, Google Drive, etc."
                  value={submissionForm.url_links}
                  onChange={(e) => setSubmissionForm({...submissionForm, url_links: e.target.value})}
                />
              </div>
              
              <div className="input-group">
                <label className="input-label">Attachment (Optional)</label>
                <input 
                  type="file" 
                  className="input-field" 
                  onChange={(e) => setSubmissionFile(e.target.files[0])}
                />
              </div>
              
              <div className="input-group">
                <label className="input-label">Visibility</label>
                <select 
                  className="input-field"
                  value={submissionForm.visibility}
                  onChange={(e) => setSubmissionForm({...submissionForm, visibility: e.target.value})}
                >
                  <option value="all">Entire Organization</option>
                  <option value="assignee_admins">Only Assignees + Admins/Owner</option>
                </select>
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1rem' }}>
                <button 
                  style={{ padding: '0.5rem 1rem', background: 'transparent', border: 'none', color: '#64748b', fontWeight: 600, cursor: 'pointer' }}
                  onClick={() => {
                    setSubmissionModalConfig({ isOpen: false, ticketId: null, taskId: null, taskTitle: '' });
                    setSubmissionForm({ comments: '', url_links: '', visibility: 'all', visible_to: [] });
                    setSubmissionFile(null);
                  }}
                  disabled={loading}
                >
                  Cancel
                </button>
                <button 
                  className="btn-primary"
                  disabled={loading || !submissionForm.comments.trim()}
                  onClick={async () => {
                    setLoading(true);
                    try {
                      const formData = new FormData();
                      formData.append('comments', submissionForm.comments);
                      formData.append('url_links', submissionForm.url_links);
                      formData.append('visibility', submissionForm.visibility);
                      if (submissionFile) {
                        formData.append('file_attachment', submissionFile);
                      }
                      
                      await submitTaskProof(submissionModalConfig.taskId, formData);
                      
                      // Now mark the ticket as done
                      if (submissionModalConfig.ticketId) {
                        await updateTaskTicketStatus(submissionModalConfig.ticketId, 'done');
                      }
                      
                      setSubmissionModalConfig({ isOpen: false, ticketId: null, taskId: null, taskTitle: '' });
                      setSubmissionForm({ comments: '', url_links: '', visibility: 'all', visible_to: [] });
                      setSubmissionFile(null);
                      
                      const updatedTask = await getOrgTaskDetail(selectedOrg.slug, activeTask.id);
                      setActiveTask(updatedTask);
                      handleLoadTasks();
                    } catch (err) {
                      console.error(err);
                      alert('Failed to submit proof.');
                    } finally {
                      setLoading(false);
                    }
                  }}
                >
                  {loading ? 'Submitting...' : 'Submit & Mark Done'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {feedbackModalConfig.isOpen && (
        <TaskFeedbackModal
          taskId={feedbackModalConfig.taskId}"""

content = content.replace(target_modal, replacement_modal)

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("App.jsx patched with Submission Modal")
