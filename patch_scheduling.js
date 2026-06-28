const fs = require('fs');
const { execSync } = require('child_process');

const appJsxPath = 'frontend/src/App.jsx';

try {
    console.log("Reverting App.jsx to Git HEAD to clear any corruption...");
    execSync(`git checkout -- ${appJsxPath}`);
    console.log("App.jsx reverted successfully.");

    console.log("Reading App.jsx...");
    let content = fs.readFileSync(appJsxPath, 'utf8');

    // Normalize all line endings to LF first to make regex and string matching clean,
    // then we will write it out as CRLF.
    content = content.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

    // 1. Update newTaskData state structure to add estimated_hours_part and estimated_minutes_part
    console.log("1. Updating newTaskData state initialization...");
    const oldNewTaskData = `  const [newTaskData, setNewTaskData] = useState({
    title: '',
    description: '',
    issue_type: 'task',
    priority: 'medium',
    status: 'todo',
    due_date: '',
    start_date: '',
    estimated_hours: '',
    estimated_minutes: '',
    reminder_preference: 'none',
    reminder_duration_minutes: '',
    required_assignees: 1,
    assignees: [],
    watchers: [],
    visibility_type: 'specific',
    visible_to: [],
    sharing_option: 'specific',
    shared_viewers: [],
    goal: '',
    impact: 5,
    risk: 'medium'
  });`;

    const newNewTaskData = `  const [newTaskData, setNewTaskData] = useState({
    title: '',
    description: '',
    issue_type: 'task',
    priority: 'medium',
    status: 'todo',
    due_date: '',
    start_date: '',
    estimated_hours: '',
    estimated_minutes: '',
    estimated_hours_part: '',
    estimated_minutes_part: '',
    reminder_preference: 'none',
    reminder_duration_minutes: '',
    required_assignees: 1,
    assignees: [],
    watchers: [],
    visibility_type: 'specific',
    visible_to: [],
    sharing_option: 'specific',
    shared_viewers: [],
    goal: '',
    impact: 5,
    risk: 'medium'
  });

  const [schedulePreview, setSchedulePreview] = useState({
    message: 'Select an Assignee and enter Estimated Hours + Minutes to see the schedule preview.',
    isLoading: false,
  });

  const [scheduledTime, setScheduledTime] = useState({
    startDate: '',
    startTime: '',
    endDate: '',
    endTime: '',
    manualOverride: false,
  });

  useEffect(() => {
    if (tasksView !== 'create') return;

    const assigneeId = newTaskData.assignees?.[0];
    const totalMins = parseInt(newTaskData.estimated_minutes, 10);

    if (assigneeId && !isNaN(totalMins) && totalMins > 0 && !scheduledTime.manualOverride) {
      setSchedulePreview(prev => ({ ...prev, isLoading: true }));
      const timer = setTimeout(async () => {
        try {
          if (selectedOrg && selectedOrg.id) {
             const estHours = totalMins / 60.0;
             const res = await api.schedulePreview(selectedOrg.id, assigneeId, estHours);
             
             const extractDate = (isoString) => isoString ? isoString.substring(0, 10) : '';
             const extractTime = (isoString) => isoString ? isoString.substring(11, 16) : '';
             
             setScheduledTime({
               startDate: extractDate(res.planned_start),
               startTime: extractTime(res.planned_start),
               endDate: extractDate(res.planned_end),
               endTime: extractTime(res.planned_end),
               manualOverride: false,
             });
             
             setSchedulePreview({
               message: res.message || '',
               isLoading: false,
             });
          }
        } catch (err) {
          console.error("Preview error", err);
          setSchedulePreview({
            message: 'Failed to fetch schedule preview',
            isLoading: false,
          });
        }
      }, 300);
      return () => clearTimeout(timer);
    } else if (!assigneeId || isNaN(totalMins) || totalMins <= 0) {
       if (!scheduledTime.manualOverride) {
         setScheduledTime({
           startDate: '',
           startTime: '',
           endDate: '',
           endTime: '',
           manualOverride: false,
         });
         setSchedulePreview({
           message: 'Select an Assignee and enter Estimated Hours + Minutes to see the schedule preview.',
           isLoading: false,
         });
       }
    }
  }, [newTaskData.assignees, newTaskData.estimated_minutes, selectedOrg, tasksView, scheduledTime.manualOverride]);`;

    if (content.includes(oldNewTaskData)) {
        content = content.replace(oldNewTaskData, newNewTaskData);
        console.log(" newTaskData state and useEffect updated.");
    } else {
        throw new Error("Could not find old newTaskData state block!");
    }

    // 2. Make form fields required (Title, Description, Goal dropdown, Priority, Issue Type, Assignee)
    console.log("2. Making fields in Create Task form HTML-required...");
    
    // Description required
    content = content.replace(
        '<textarea\n                            rows={4}\n                            className="task-form-input"\n                            style={{ resize: \'vertical\', minHeight: \'100px\' }}\n                            placeholder="Add details, acceptance criteria, etc..."\n                            value={newTaskData.description}\n                            onChange={(e) => setNewTaskData({...newTaskData, description: e.target.value})}\n                          />',
        '<textarea\n                            required\n                            rows={4}\n                            className="task-form-input"\n                            style={{ resize: \'vertical\', minHeight: \'100px\' }}\n                            placeholder="Add details, acceptance criteria, etc..."\n                            value={newTaskData.description}\n                            onChange={(e) => setNewTaskData({...newTaskData, description: e.target.value})}\n                          />'
    );

    // Goal Dropdown required & change options
    const oldGoalSelect = `<select
                            className="task-form-select"
                            value={newTaskData.goal || ''}
                            onChange={(e) => setNewTaskData({...newTaskData, goal: e.target.value || ''})}
                          >
                            <option value="">No Goal Linked</option>
                            {goals.map(g => (
                              <option key={g.id} value={g.id}>{g.title}</option>
                            ))}
                          </select>`;
                          
    const newGoalSelect = `<select
                            required
                            className="task-form-select"
                            value={newTaskData.goal || ''}
                            onChange={(e) => setNewTaskData({...newTaskData, goal: e.target.value})}
                          >
                            <option value="" disabled>Select a Goal</option>
                            {goals.map(g => (
                              <option key={g.id} value={g.id}>{g.title}</option>
                            ))}
                          </select>`;

    if (content.includes(oldGoalSelect)) {
        content = content.replace(oldGoalSelect, newGoalSelect);
        console.log(" Goal dropdown updated to be required.");
    } else {
        throw new Error("Could not find old Goal select block!");
    }

    // Estimated Hours + Minutes inputs (replace old 3-column grid)
    console.log("3. Replacing Est. Hours / Minutes input fields with two required inputs...");
    const oldEstGrid = `<div className="task-form-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
                          <div className="task-form-group">
                            <label className="task-form-label">Est. Hours</label>
                            <input
                              type="number"
                              step="0.1"
                              min="0"
                              className="task-form-input"
                              placeholder="e.g. 1.5"
                              value={newTaskData.estimated_hours || ''}
                              onChange={(e) => {
                                const val = e.target.value;
                                setNewTaskData(prev => ({
                                  ...prev,
                                  estimated_hours: val,
                                  estimated_minutes: val !== '' ? Math.round(parseFloat(val) * 60) : ''
                                }));
                              }}
                            />
                          </div>
                          <div className="task-form-group">
                            <label className="task-form-label">Est. Minutes</label>
                            <input
                              type="number"
                              min="0"
                              className="task-form-input"
                              placeholder="e.g. 90"
                              value={newTaskData.estimated_minutes || ''}
                              onChange={(e) => {
                                const val = e.target.value;
                                setNewTaskData(prev => ({
                                  ...prev,
                                  estimated_minutes: val,
                                  estimated_hours: val !== '' ? (parseInt(val, 10) / 60).toFixed(2) : ''
                                }));
                              }}
                            />
                          </div>
                          <div className="task-form-group">
                            <label className="task-form-label">Manual Due Date (Optional)</label>
                            <input
                              type="date"
                              className="task-form-input"
                              value={newTaskData.due_date || ''}
                              onChange={(e) => setNewTaskData({...newTaskData, due_date: e.target.value})}
                            />
                          </div>
                        </div>`;

    const newEstGrid = `<div className="task-form-grid" style={{ gridTemplateColumns: 'repeat(2, 1fr)' }}>
                          <div className="task-form-group">
                            <label className="task-form-label">Est. Hours</label>
                            <input
                              type="number"
                              required
                              min="0"
                              className="task-form-input"
                              placeholder="Hours"
                              value={newTaskData.estimated_hours_part || ''}
                              onChange={(e) => {
                                const val = e.target.value;
                                const hours = val !== '' ? parseInt(val, 10) : 0;
                                const mins = newTaskData.estimated_minutes_part !== '' ? parseInt(newTaskData.estimated_minutes_part, 10) : 0;
                                const totalMins = (hours * 60) + mins;
                                const totalHours = totalMins / 60;
                                setNewTaskData(prev => ({
                                  ...prev,
                                  estimated_hours_part: val,
                                  estimated_hours: totalMins > 0 ? totalHours.toFixed(2) : '',
                                  estimated_minutes: totalMins > 0 ? totalMins : '',
                                }));
                              }}
                            />
                          </div>
                          <div className="task-form-group">
                            <label className="task-form-label">Est. Minutes</label>
                            <input
                              type="number"
                              required
                              min="0"
                              max="59"
                              className="task-form-input"
                              placeholder="Minutes"
                              value={newTaskData.estimated_minutes_part || ''}
                              onChange={(e) => {
                                const val = e.target.value;
                                const hours = newTaskData.estimated_hours_part !== '' ? parseInt(newTaskData.estimated_hours_part, 10) : 0;
                                const mins = val !== '' ? parseInt(val, 10) : 0;
                                const totalMins = (hours * 60) + mins;
                                const totalHours = totalMins / 60;
                                setNewTaskData(prev => ({
                                  ...prev,
                                  estimated_minutes_part: val,
                                  estimated_hours: totalMins > 0 ? totalHours.toFixed(2) : '',
                                  estimated_minutes: totalMins > 0 ? totalMins : '',
                                }));
                              }}
                            />
                          </div>
                        </div>`;

    if (content.includes(oldEstGrid)) {
        content = content.replace(oldEstGrid, newEstGrid);
        console.log(" Estimated Hours/Minutes input fields updated.");
    } else {
        throw new Error("Could not find old estimated hours/minutes grid!");
    }

    // Assignee dropdown: make required and change Option
    console.log("4. Updating Assignee dropdown select...");
    const oldAssigneeSelect = `<select
                                className="task-form-select"
                                value={newTaskData.assignees && newTaskData.assignees[0] || ''}
                                onChange={(e) => {
                                  const val = e.target.value;
                                  setNewTaskData(prev => ({
                                    ...prev,
                                    assignees: val ? [val] : []
                                  }));
                                }}
                              >
                                <option value="">Unassigned</option>
                                {orgMembers.map(m => {
                                  const userId = m.user?.id || m.user_id;
                                  const name = m.user?.first_name || m.user?.last_name ? \`\${m.user.first_name || ''} \${m.user.last_name || ''}\`.trim() : m.email;
                                  return (
                                    <option key={userId} value={userId}>
                                      {name}
                                    </option>
                                  );
                                })}
                              </select>`;

    const newAssigneeSelect = `<select
                                required
                                className="task-form-select"
                                value={newTaskData.assignees && newTaskData.assignees[0] || ''}
                                onChange={(e) => {
                                  const val = e.target.value;
                                  setNewTaskData(prev => ({
                                    ...prev,
                                    assignees: val ? [val] : []
                                  }));
                                }}
                              >
                                <option value="" disabled>Select Assignee</option>
                                {orgMembers.map(m => {
                                  const userId = m.user?.id || m.user_id;
                                  const name = m.user?.first_name || m.user?.last_name ? \`\${m.user.first_name || ''} \${m.user.last_name || ''}\`.trim() : m.email;
                                  return (
                                    <option key={userId} value={userId}>
                                      {name}
                                    </option>
                                  );
                                })}
                              </select>`;

    if (content.includes(oldAssigneeSelect)) {
        content = content.replace(oldAssigneeSelect, newAssigneeSelect);
        console.log(" Assignee select dropdown updated to be required.");
    } else {
        throw new Error("Could not find old Assignee select dropdown!");
    }

    // 5. Scheduled Time section after Assignment section
    console.log("5. Injecting Scheduled Time section after Assignment section...");
    
    // The Sharing & Permissions label block is right after the Assignment block
    const targetSharingBlock = `<label className="task-form-label">Sharing & Permissions</label>`;
    
    const newScheduledTimeSection = `{/* Scheduled Time Section */}
                        <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.25rem', marginBottom: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                          <h4 style={{ margin: 0, fontSize: '0.85rem', fontWeight: 700, color: '#4f46e5', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            📅 Scheduled Time
                            {schedulePreview.isLoading && <div style={{ border: '2px solid #e2e8f0', borderTop: '2px solid #6366f1', borderRadius: '50%', width: '12px', height: '12px', animation: 'spin 1s linear infinite' }} />}
                          </h4>
                          
                          <div className="task-form-grid" style={{ gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem', marginBottom: 0 }}>
                            <div className="task-form-group" style={{ marginBottom: 0 }}>
                              <label className="task-form-label">Start Date</label>
                              <input 
                                type="date" 
                                className="task-form-input" 
                                value={scheduledTime.startDate} 
                                onChange={(e) => setScheduledTime(prev => ({ ...prev, startDate: e.target.value, manualOverride: true }))}
                              />
                            </div>
                            <div className="task-form-group" style={{ marginBottom: 0 }}>
                              <label className="task-form-label">Start Time</label>
                              <input 
                                type="time" 
                                className="task-form-input" 
                                value={scheduledTime.startTime} 
                                onChange={(e) => setScheduledTime(prev => ({ ...prev, startTime: e.target.value, manualOverride: true }))}
                              />
                            </div>
                          </div>

                          <div className="task-form-grid" style={{ gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem', marginBottom: 0 }}>
                            <div className="task-form-group" style={{ marginBottom: 0 }}>
                              <label className="task-form-label">End Date</label>
                              <input 
                                type="date" 
                                className="task-form-input" 
                                value={scheduledTime.endDate} 
                                onChange={(e) => setScheduledTime(prev => ({ ...prev, endDate: e.target.value, manualOverride: true }))}
                              />
                            </div>
                            <div className="task-form-group" style={{ marginBottom: 0 }}>
                              <label className="task-form-label">End Time</label>
                              <input 
                                type="time" 
                                className="task-form-input" 
                                value={scheduledTime.endTime} 
                                onChange={(e) => setScheduledTime(prev => ({ ...prev, endTime: e.target.value, manualOverride: true }))}
                              />
                            </div>
                          </div>

                          {schedulePreview.message && !schedulePreview.isLoading && (
                            <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '0.25rem', fontStyle: 'italic' }}>
                              {schedulePreview.message}
                            </div>
                          )}
                        </div>

                        <label className="task-form-label">Sharing & Permissions</label>`;

    if (content.includes(targetSharingBlock)) {
        content = content.replace(targetSharingBlock, newScheduledTimeSection);
        console.log(" Scheduled Time section added after Assignment block.");
    } else {
        throw new Error("Could not find Sharing & Permissions label block!");
    }

    // 6. Payload modification: send planned_start and planned_end
    console.log("6. Updating payload submit logic...");
    const oldPayload = `                          const payload = {
                            ...newTaskData,
                            organization: selectedOrg.id
                          };`;
                          
    const newPayload = `                          const payload = {
                            ...newTaskData,
                            organization: selectedOrg.id
                          };
                          
                          if (scheduledTime.startDate && scheduledTime.startTime) {
                             payload.planned_start = \`\${scheduledTime.startDate}T\${scheduledTime.startTime}:00\`;
                          }
                          if (scheduledTime.endDate && scheduledTime.endTime) {
                             payload.planned_end = \`\${scheduledTime.endDate}T\${scheduledTime.endTime}:00\`;
                          }`;

    if (content.includes(oldPayload)) {
        content = content.replace(oldPayload, newPayload);
        console.log(" Payload logic updated.");
    } else {
        throw new Error("Could not find old payload block!");
    }

    // 7. Reset state inside submit handler
    console.log("7. Updating state resets in submit handler...");
    const oldReset = `                          setNewTaskData({
                            title: '', description: '', issue_type: 'task', priority: 'medium',
                            status: 'todo', due_date: '', start_date: '', estimated_hours: '', assignees: [],
                            watchers: [], visibility_type: 'specific', visible_to: [], goal: '',
                            sharing_option: 'specific', shared_viewers: [],
                            due_time: '', estimated_minutes: '', reminder_preference: 'none', reminder_duration_minutes: '',
                            required_assignees: 1,
                            impact: 5,
                            risk: 'medium'
                          });`;

    const newReset = `                          setNewTaskData({
                            title: '', description: '', issue_type: 'task', priority: 'medium',
                            status: 'todo', due_date: '', start_date: '', estimated_hours: '', assignees: [],
                            watchers: [], visibility_type: 'specific', visible_to: [], goal: '',
                            sharing_option: 'specific', shared_viewers: [],
                            due_time: '', estimated_minutes: '', reminder_preference: 'none', reminder_duration_minutes: '',
                            required_assignees: 1,
                            impact: 5,
                            risk: 'medium',
                            estimated_hours_part: '',
                            estimated_minutes_part: ''
                          });
                          setScheduledTime({
                            startDate: '',
                            startTime: '',
                            endDate: '',
                            endTime: '',
                            manualOverride: false,
                          });
                          setSchedulePreview({
                            message: 'Select an Assignee and enter Estimated Hours + Minutes to see the schedule preview.',
                            isLoading: false,
                          });`;

    if (content.includes(oldReset)) {
        content = content.replace(oldReset, newReset);
        console.log(" Reset state logic updated.");
    } else {
        throw new Error("Could not find old reset block!");
    }

    // 8. Success message formatting
    console.log("8. Updating success message formatting function...");
    const oldSuccessFormat = `function formatTaskCreateSuccess(response) {
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

    const newSuccessFormat = `function formatTaskCreateSuccess(response) {
  const task = response.task || response;
  
  if (task.planned_start && task.planned_end && task.schedule_status === 'SCHEDULED') {
    const parseISO = (isoStr) => {
      try {
        const parts = isoStr.split('T');
        const dateParts = parts[0].split('-');
        const timeParts = parts[1].substring(0, 8).split(':');
        
        const year = parseInt(dateParts[0], 10);
        const month = parseInt(dateParts[1], 10) - 1;
        const day = parseInt(dateParts[2], 10);
        const hour = parseInt(timeParts[0], 10);
        const minute = parseInt(timeParts[1], 10);
        
        return { year, month, day, hour, minute };
      } catch (e) {
        return null;
      }
    };

    const start = parseISO(task.planned_start);
    const end = parseISO(task.planned_end);

    if (start && end) {
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      const dateStr = \`\${start.day} \${months[start.month]} \${start.year}\`;

      const formatTime = (timeObj) => {
        let h = timeObj.hour;
        const m = String(timeObj.minute).padStart(2, '0');
        const ampm = h >= 12 ? 'PM' : 'AM';
        h = h % 12;
        h = h ? h : 12;
        const hStr = String(h).padStart(2, '0');
        return \`\${hStr}:\${m} \${ampm}\`;
      };

      const startStr = formatTime(start);
      const endStr = formatTime(end);

      return \`✅ Task created successfully!\\nScheduled on \${dateStr} from \${startStr} to \${endStr}\`;
    }
  }

  return \`✅ Task created successfully!\\nNo available slot found. Task is QUEUED.\`;
}`;

    if (content.includes(oldSuccessFormat)) {
        content = content.replace(oldSuccessFormat, newSuccessFormat);
        console.log(" Success message formatting function updated.");
    } else {
        throw new Error("Could not find old success message formatting function!");
    }

    // Write back content with Windows line endings
    content = content.replace(/\n/g, '\r\n');
    fs.writeFileSync(appJsxPath, content, 'utf8');
    console.log("App.jsx updated and normalized to CRLF successfully!");
} catch (e) {
    console.error("❌ Patching failed:", e.message);
}
