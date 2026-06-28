import sys
import re

app_jsx_path = r'c:\Users\saura\ParseOps\frontend\src\App.jsx'

print(f"Reading {app_jsx_path}...")
with open(app_jsx_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Normalize line endings to avoid vite parse errors
content = content.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '\r\n')

def build_regex(text):
    return re.sub(r'\s+', r'\\s+', re.escape(text.strip()))

# 1. State and useEffect addition
state_insertion_point = "  const [newTaskData, setNewTaskData] = useState({"
state_additions = """  const [schedulePreview, setSchedulePreview] = useState({
    planned_start: '',
    planned_end: '',
    message: 'Select an Assignee and enter Estimated Hours to see the schedule preview.',
    status: '',
    isLoading: false,
    manualOverride: false,
  });

  useEffect(() => {
    // Only run when create task modal is open or view is task list
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
  }, [newTaskData.assignees, newTaskData.estimated_hours, selectedOrg, showCreateModal, view, schedulePreview.manualOverride]);

  const [newTaskData, setNewTaskData] = useState({"""

print("Injecting schedulePreview state and useEffect...")
content = content.replace(state_insertion_point, state_additions)


# 2. Add fields to UI (Impact, Risk)
priority_issue_block = """                        <div className="task-form-grid">

                          <div className="task-form-group">

                            <label className="task-form-label">Priority</label>

                            <select

                              className="task-form-select"

                              value={newTaskData.priority}

                              onChange={(e) => setNewTaskData({...newTaskData, priority: e.target.value})}

                            >

                              <option value="low">Low</option>

                              <option value="medium">Medium</option>

                              <option value="high">High</option>

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

                        </div>"""

new_priority_issue_block = """                        <div className="task-form-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
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
                        </div>"""

print("Replacing Priority/Issue Type block with Impact/Risk fields...")
content = re.sub(build_regex(priority_issue_block), new_priority_issue_block, content, count=1)


# 3. Schedule Preview Block before the create button
submit_buttons_block = """                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem', paddingTop: '1.25rem', borderTop: '1px solid #f1f5f9' }}>

                          <button type="button" onClick={() => setTasksView('list')} className="btn-secondary" style={{ width: 'auto', padding: '0.6rem 1.2rem' }}>Cancel</button>

                          <button type="submit" disabled={loading} className="btn-primary" style={{ width: 'auto', padding: '0.6rem 1.5rem' }}>{loading ? 'Creating...' : 'Create Task'}</button>

                        </div>"""

new_submit_buttons_block = """                        <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '1rem', marginBottom: '1rem', marginTop: '1rem' }}>
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

                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem', paddingTop: '1.25rem', borderTop: '1px solid #f1f5f9' }}>
                          <button type="button" onClick={() => setTasksView('list')} className="btn-secondary" style={{ width: 'auto', padding: '0.6rem 1.2rem' }}>Cancel</button>
                          <button type="submit" disabled={loading} className="btn-primary" style={{ width: 'auto', padding: '0.6rem 1.5rem' }}>{loading ? 'Creating...' : 'Create Task'}</button>
                        </div>"""

print("Injecting Schedule Preview box...")
content = re.sub(build_regex(submit_buttons_block), new_submit_buttons_block, content, count=1)


# 4. Modify Handle Submit payload
payload_block = """                          const payload = {

                            ...newTaskData,

                            organization: selectedOrg.id

                          };"""

new_payload_block = """                          const payload = {
                            ...newTaskData,
                            organization: selectedOrg.id
                          };
                          
                          if (schedulePreview.planned_start && schedulePreview.planned_end) {
                             // Convert local datetime-local string to ISO string for backend
                             payload.planned_start = new Date(schedulePreview.planned_start).toISOString();
                             payload.planned_end = new Date(schedulePreview.planned_end).toISOString();
                          }"""

print("Updating API payload logic...")
content = re.sub(build_regex(payload_block), new_payload_block, content, count=1)


# 5. Format Task Create Success function update
success_format_block = """function formatTaskCreateSuccess(response) {
  const task = response.task || response;
  const details = response.scheduled_details || {};

  if (details.status === 'SCHEDULED' && details.scheduled_date && details.start_time && details.end_time) {
    return [
      'Task created successfully!',
      '',
      `Scheduled Date: ${details.scheduled_date}`,
      `Start Time: ${details.start_time}`,
      `End Time: ${details.end_time}`,
      'Status: SCHEDULED',
    ].join('\\n');
  }

  if (task.planned_start && task.planned_end && task.schedule_status === 'SCHEDULED') {
    const startDate = new Date(task.planned_start);
    const endDate = new Date(task.planned_end);
    const dateStr = startDate.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
    const startStr = startDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
    const endStr = endDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });

    return [
      'Task created successfully!',
      '',
      `Scheduled Date: ${dateStr}`,
      `Start Time: ${startStr}`,
      `End Time: ${endStr}`,
      'Status: SCHEDULED',
    ].join('\\n');
  }

  return [
    'Task created successfully!',
    '',
    'Status: QUEUED',
    'No available slot found within the next 7 working days. Task is QUEUED.',
  ].join('\\n');
}"""

new_success_format_block = """function formatTaskCreateSuccess(response) {
  const task = response.task || response;
  
  if (task.planned_start && task.planned_end && task.schedule_status === 'SCHEDULED') {
    const startDate = new Date(task.planned_start);
    const endDate = new Date(task.planned_end);
    const dateStr = startDate.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
    const startStr = startDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
    const endStr = endDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });

    return `✅ Task created successfully!\\n\\n📅 Scheduled on ${dateStr} from ${startStr} to ${endStr}`;
  }

  return `✅ Task created successfully!\\n\\n⚠️ No available slot found. Task is QUEUED.`;
}"""

print("Formatting success message...")
content = re.sub(build_regex(success_format_block), new_success_format_block, content, count=1)


# 6. Reset state after create
reset_block = """                          setNewTaskData({

                            title: '', description: '', issue_type: 'task', priority: 'medium',

                            status: 'todo', due_date: '', start_date: '', estimated_hours: '', assignees: [],

                            watchers: [], visibility_type: 'specific', visible_to: [], goal: '',

                            sharing_option: 'specific', shared_viewers: [],

                            due_time: '', estimated_minutes: '', reminder_preference: 'none', reminder_duration_minutes: '',

                            required_assignees: 1,

                            impact: 5,

                            risk: 'medium'

                          });"""

new_reset_block = """                          setNewTaskData({
                            title: '', description: '', issue_type: 'task', priority: 'medium',
                            status: 'todo', due_date: '', start_date: '', estimated_hours: '', assignees: [],
                            watchers: [], visibility_type: 'specific', visible_to: [], goal: '',
                            sharing_option: 'specific', shared_viewers: [],
                            due_time: '', estimated_minutes: '', reminder_preference: 'none', reminder_duration_minutes: '',
                            required_assignees: 1,
                            impact: 5,
                            risk: 'medium'
                          });
                          setSchedulePreview({ planned_start: '', planned_end: '', message: 'Select an Assignee and enter Estimated Hours to see the schedule preview.', status: '', isLoading: false, manualOverride: false });"""

print("Updating reset state...")
content = re.sub(build_regex(reset_block), new_reset_block, content, count=1)

with open(app_jsx_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Frontend App.jsx patched successfully! You can verify the changes now.")
