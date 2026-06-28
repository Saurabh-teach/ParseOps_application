const fs = require('fs');
const { execSync } = require('child_process');

try {
    console.log("Restoring original App.jsx from Git...");
    let content = execSync('git show HEAD:frontend/src/App.jsx', { encoding: 'utf8' });
    content = content.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

    const newTaskDataRegex = /(  const \[newTaskData, setNewTaskData\] = useState\(\{[\s\S]*?risk: 'medium'\n  \}\);)/;
    const schedulePreviewBlock = `

  const [schedulePreview, setSchedulePreview] = useState({
    planned_start: '',
    planned_end: '',
    message: 'Select an Assignee and enter Estimated Hours to see the schedule preview.',
    status: '',
    isLoading: false,
    manualOverride: false,
  });

  useEffect(() => {
    if (!showCreateModal && view !== 'dashboard') return;

    const assigneeId = newTaskData.assignees?.[0];
    const estHours = parseFloat(newTaskData.estimated_hours);

    if (assigneeId && !isNaN(estHours) && estHours > 0 && !schedulePreview.manualOverride) {
      setSchedulePreview(prev => ({ ...prev, isLoading: true }));
      const timer = setTimeout(async () => {
        try {
          if (selectedOrg && selectedOrg.id) {
             const res = await api.schedulePreview(selectedOrg.id, assigneeId, estHours);
             const formatForInput = (isoString) => {
                if (!isoString) return '';
                const d = new Date(isoString);
                d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
                return d.toISOString().slice(0, 16);
             };
             setSchedulePreview(prev => ({
               ...prev,
               planned_start: formatForInput(res.planned_start),
               planned_end: formatForInput(res.planned_end),
               message: res.message || 'Slot found.',
               status: res.planned_start ? 'SCHEDULED' : 'QUEUED',
               isLoading: false
             }));
          }
        } catch (err) {
          console.error("Preview error", err);
          setSchedulePreview(prev => ({ ...prev, isLoading: false, message: 'Failed to fetch schedule preview' }));
        }
      }, 300);
      return () => clearTimeout(timer);
    } else if (!assigneeId || isNaN(estHours) || estHours <= 0) {
       if (!schedulePreview.manualOverride) {
           setSchedulePreview({ planned_start: '', planned_end: '', message: 'Select an Assignee and enter Estimated Hours to see the schedule preview.', status: '', isLoading: false, manualOverride: false });
       }
    }
  }, [newTaskData.assignees, newTaskData.estimated_hours, selectedOrg, showCreateModal, view, schedulePreview.manualOverride]);`;

    content = content.replace(newTaskDataRegex, '$1' + schedulePreviewBlock);

    const newPriorityBlock = `                        <div className="task-form-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
                          <div className="task-form-group">
                            <label className="task-form-label">Priority</label>
                            <select
                              className="task-form-select"
                              value={newTaskData.priority}
                              onChange={(e) => setNewTaskData({...newTaskData, priority: e.target.value})}
                            >
                              <option value="high">High</option>
                              <option value="medium">Medium</option>
                              <option value="low">Low</option>
                            </select>
                          </div>
                          <div className="task-form-group">
                            <label className="task-form-label">Issue Type</label>
                            <select
                              className="task-form-select"
                              value={newTaskData.issue_type}
                              onChange={(e) => setNewTaskData({...newTaskData, issue_type: e.target.value})}
                            >
                              <option value="task">Task</option>
                              <option value="bug">Bug</option>
                              <option value="story">Story</option>
                            </select>
                          </div>
                          <div className="task-form-group">
                            <label className="task-form-label">Impact</label>
                            <select
                              className="task-form-select"
                              value={newTaskData.impact}
                              onChange={(e) => setNewTaskData({...newTaskData, impact: parseInt(e.target.value)})}
                            >
                              <option value={8}>High</option>
                              <option value={5}>Medium</option>
                              <option value={2}>Low</option>
                            </select>
                          </div>
                          <div className="task-form-group">
                            <label className="task-form-label">Risk</label>
                            <select
                              className="task-form-select"
                              value={newTaskData.risk}
                              onChange={(e) => setNewTaskData({...newTaskData, risk: e.target.value})}
                            >
                              <option value="high">High</option>
                              <option value="medium">Medium</option>
                              <option value="low">Low</option>
                            </select>
                          </div>
                        </div>`;
    content = content.replace(/<div className="task-form-grid">\s*<div className="task-form-group">\s*<label className="task-form-label">Priority[\s\S]*?<\/option>\s*<\/select>\s*<\/div>\s*<\/div>/, newPriorityBlock);

    const submitBlockRegex = /(<div style=\{\{ display: 'flex', justifyContent: 'flex-end', gap: '0\.75rem', marginTop: '1rem', paddingTop: '1\.25rem', borderTop: '1px solid #f1f5f9' \}\}>\s*<button type="button" onClick=\{\(\) => setTasksView\('list'\)\} className="btn-secondary" style=\{\{ width: 'auto', padding: '0\.6rem 1\.2rem' \}\}>Cancel<\/button>\s*<button type="submit" disabled=\{loading\} className="btn-primary" style=\{\{ width: 'auto', padding: '0\.6rem 1\.5rem' \}\}>\{loading \? 'Creating\.\.\.' : 'Create Task'\}<\/button>\s*<\/div>)/;
    
    const newSubmitBlock = `                        <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '1rem', marginBottom: '1rem', marginTop: '1rem' }}>
                          <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '0.9rem', color: '#1e293b', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            📅 Schedule Preview
                            {schedulePreview.isLoading && <div style={{ border: '2px solid #e2e8f0', borderTop: '2px solid #6366f1', borderRadius: '50%', width: '12px', height: '12px', animation: 'spin 1s linear infinite' }} />}
                          </h4>
                          
                          {schedulePreview.status === 'SCHEDULED' || schedulePreview.manualOverride ? (
                            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                              <div style={{ flex: 1 }}>
                                <label style={{ display: 'block', fontSize: '0.75rem', color: '#64748b', marginBottom: '0.25rem' }}>Planned Start</label>
                                <input 
                                  type="datetime-local" 
                                  className="task-form-input" 
                                  style={{ padding: '0.4rem', fontSize: '0.85rem' }}
                                  value={schedulePreview.planned_start} 
                                  onChange={(e) => setSchedulePreview(prev => ({ ...prev, planned_start: e.target.value, manualOverride: true }))}
                                />
                              </div>
                              <div style={{ flex: 1 }}>
                                <label style={{ display: 'block', fontSize: '0.75rem', color: '#64748b', marginBottom: '0.25rem' }}>Planned End</label>
                                <input 
                                  type="datetime-local" 
                                  className="task-form-input" 
                                  style={{ padding: '0.4rem', fontSize: '0.85rem' }}
                                  value={schedulePreview.planned_end} 
                                  onChange={(e) => setSchedulePreview(prev => ({ ...prev, planned_end: e.target.value, manualOverride: true }))}
                                />
                              </div>
                            </div>
                          ) : (
                            <div style={{ fontSize: '0.85rem', color: '#64748b' }}>
                              {schedulePreview.message}
                            </div>
                          )}
                        </div>

                        $1`;
    content = content.replace(submitBlockRegex, newSubmitBlock);

    const payloadRegex = /(const payload = \{\s*\.\.\.newTaskData,\s*organization: selectedOrg\.id\s*\};)/;
    const newPayloadBlock = `$1
                          
                          if (schedulePreview.planned_start && schedulePreview.planned_end) {
                             payload.planned_start = new Date(schedulePreview.planned_start).toISOString();
                             payload.planned_end = new Date(schedulePreview.planned_end).toISOString();
                          }`;
    content = content.replace(payloadRegex, newPayloadBlock);

    const resetRegex = /(setNewTaskData\(\{[\s\S]*?risk: 'medium'\s*\}\);)/;
    content = content.replace(resetRegex, `$1\n                          setSchedulePreview({ planned_start: '', planned_end: '', message: 'Select an Assignee and enter Estimated Hours to see the schedule preview.', status: '', isLoading: false, manualOverride: false });`);

    const successRegex = /function formatTaskCreateSuccess\(response\) \{[\s\S]*?QUEUED\.',\s*\]\.join\('\\n'\);\s*\}/;
    const newSuccessBlock = `function formatTaskCreateSuccess(response) {
  const task = response.task || response;
  
  if (task.planned_start && task.planned_end && task.schedule_status === 'SCHEDULED') {
    const startDate = new Date(task.planned_start);
    const endDate = new Date(task.planned_end);
    const dateStr = startDate.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
    const startStr = startDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
    const endStr = endDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });

    return \`✅ Task created successfully!\\n\\n📅 Scheduled on \${dateStr} from \${startStr} to \${endStr}\`;
  }

  return \`✅ Task created successfully!\\n\\n⚠️ No available slot found. Task is QUEUED.\`;
}`;
    content = content.replace(successRegex, newSuccessBlock);

    fs.writeFileSync('frontend/src/App.jsx', content, 'utf8');
    fs.writeFileSync('recovery_success.txt', 'SUCCESS', 'utf8');
} catch (err) {
    fs.writeFileSync('recovery_error.txt', err.toString(), 'utf8');
}
