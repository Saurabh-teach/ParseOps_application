import { useState } from 'react';
import { manualScheduleTasks, updateOrgTask } from '../api';
import { Calendar, AlertCircle, CheckCircle, User, Play, Clock, PlusCircle } from 'lucide-react';

// ─── Scheduling Helpers ────────────────────────────────────────────────────────
export const parseTime = (timeStr) => {
  if (!timeStr) return 0;
  const [h, m] = timeStr.split(':').map(Number);
  return h * 60 + m;
};

export const formatTime = (minutes) => {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  const ampm = h >= 12 ? 'PM' : 'AM';
  const h12 = h % 12 || 12;
  const mStr = m.toString().padStart(2, '0');
  return `${h12}:${mStr} ${ampm}`;
};

export const formatTime24 = (minutes) => {
  const h = Math.floor(minutes / 60).toString().padStart(2, '0');
  const m = (minutes % 60).toString().padStart(2, '0');
  return `${h}:${m}`;
};

/**
 * getAllTimeGaps
 * Returns all unbooked gaps between tasks on a timeline (0 to 24*60 mins).
 */
export const getAllTimeGaps = (tasks) => {
  if (!tasks || tasks.length === 0) return [{ start: 0, end: 24 * 60 }];
  
  const sorted = [...tasks].sort((a, b) => parseTime(a.startTime) - parseTime(b.startTime));
  
  const gaps = [];
  let currentEnd = 0; // start of day

  for (const task of sorted) {
    const taskStart = parseTime(task.startTime);
    const taskEnd = parseTime(task.endTime);

    if (taskStart > currentEnd) {
      gaps.push({ start: currentEnd, end: taskStart });
    }
    if (taskEnd > currentEnd) {
      currentEnd = taskEnd;
    }
  }

  if (currentEnd < 24 * 60) {
    gaps.push({ start: currentEnd, end: 24 * 60 });
  }

  return gaps;
};

/**
 * hasOverlap
 * Check if two time slots overlap
 */
export const hasOverlap = (start1, end1, start2, end2) => {
  const s1 = parseTime(start1);
  const e1 = parseTime(end1);
  const s2 = parseTime(start2);
  const e2 = parseTime(end2);
  return !(e1 <= s2 || e2 <= s1);
};

/**
 * findEarliestAvailableSlot
 * Finds earliest available gap for new task
 */
export const findEarliestAvailableSlot = (tasks, newTaskDuration, excludeTaskId = null) => {
  if (!tasks || tasks.length === 0) {
    return {
      startTime: "09:00",
      endTime: formatTime24(parseTime("09:00") + newTaskDuration),
      isGapFilled: true,
    };
  }

  // Sort tasks by start time
  const sortedTasks = [...tasks]
    .filter(t => t.id !== excludeTaskId)
    .sort((a, b) => parseTime(a.startTime) - parseTime(b.startTime));

  // Check gap before the first task
  const firstStart = parseTime(sortedTasks[0].startTime);
  const defaultStart = parseTime("09:00");
  if (firstStart - defaultStart >= newTaskDuration) {
    return {
      startTime: "09:00",
      endTime: formatTime24(defaultStart + newTaskDuration),
      isGapFilled: true,
    };
  }

  // Check gaps between tasks
  for (let i = 0; i < sortedTasks.length - 1; i++) {
    const currentEnd = parseTime(sortedTasks[i].endTime);
    const nextStart = parseTime(sortedTasks[i + 1].startTime);
    const gapMinutes = nextStart - currentEnd;

    if (gapMinutes >= newTaskDuration) {
      return {
        startTime: formatTime24(currentEnd),
        endTime: formatTime24(currentEnd + newTaskDuration),
        isGapFilled: true,
      };
    }
  }

  // No gap found -> put after last task
  const lastEnd = sortedTasks.length > 0
    ? parseTime(sortedTasks[sortedTasks.length - 1].endTime)
    : parseTime("09:00");
  
  return {
    startTime: formatTime24(lastEnd),
    endTime: formatTime24(lastEnd + newTaskDuration),
    isGapFilled: false,
  };
};

/**
 * rescheduleSubsequentTasks
 * Handles cascading shift when a task time is updated to prevent gaps/overlaps.
 */
export const rescheduleSubsequentTasks = (tasks, changedTaskId, newStartTime, newEndTime) => {
  const originalTask = tasks.find(t => t.id === changedTaskId);
  if (!originalTask) return tasks;

  const oldEnd = parseTime(originalTask.endTime);
  const newEndMinutes = parseTime(newEndTime);
  const delta = newEndMinutes - oldEnd;
  const originalTaskStart = parseTime(originalTask.startTime);

  let updatedTasks = tasks.map(t => {
    if (t.id === changedTaskId) {
      return { ...t, startTime: newStartTime, endTime: newEndTime };
    }
    // Shift tasks that originally started at or after the changed task
    if (parseTime(t.startTime) >= originalTaskStart) {
      const s = Math.max(0, parseTime(t.startTime) + delta);
      const e = Math.max(0, parseTime(t.endTime) + delta);
      return { ...t, startTime: formatTime24(s), endTime: formatTime24(e) };
    }
    return t;
  });

  // Sort by start time. In case of tie, the changed task comes first (so it pushes the other one).
  updatedTasks.sort((a, b) => {
    const diff = parseTime(a.startTime) - parseTime(b.startTime);
    if (diff === 0) {
      return a.id === changedTaskId ? -1 : (b.id === changedTaskId ? 1 : 0);
    }
    return diff;
  });

  // Cascade shift to ensure no overlaps anywhere
  let currentEnd = 0;
  for (let i = 0; i < updatedTasks.length; i++) {
    const task = updatedTasks[i];
    let start = parseTime(task.startTime);
    const duration = parseTime(task.endTime) - parseTime(task.startTime);
    
    // If this task starts before the previous task ended, push it to currentEnd
    if (start < currentEnd) {
      start = currentEnd;
    }
    
    updatedTasks[i] = {
      ...task,
      startTime: formatTime24(start),
      endTime: formatTime24(start + duration)
    };
    
    currentEnd = start + duration;
  }

  return updatedTasks;
};
// ─── Component ────────────────────────────────────────────────────────────────
export default function ScheduleTasksModal({ isOpen, onClose, selectedOrg, orgMembers, tasks, handleLoadTasks }) {
  const [loading, setLoading]               = useState(false);
  const [assigningTaskId, setAssigningTaskId] = useState(null);
  const [selectedMemberId, setSelectedMemberId] = useState('');
  const [searchQuery, setSearchQuery]       = useState('');
  const [error, setError]                   = useState(null);
  const [scheduleResult, setScheduleResult] = useState(null); // holds the API result after scheduling

  // Local state for the Interactive Schedule Builder
  const [localScheduleTasks, setLocalScheduleTasks] = useState([
    { id: 't1', title: 'Morning Standup', startTime: '09:00', endTime: '09:30', memberId: '' },
    { id: 't2', title: 'Code Review', startTime: '10:00', endTime: '11:00', memberId: '' }
  ]);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [newTaskDuration, setNewTaskDuration] = useState('60');
  const [newTaskMember, setNewTaskMember] = useState('');
  const [previewSchedule, setPreviewSchedule] = useState(null);

  if (!isOpen) return null;

  // ── Filters ────────────────────────────────────────────────────────────────
  let activeTasks = (tasks || []).filter(t => !t.is_deleted && t.status !== 'done');

  if (selectedMemberId) {
    activeTasks = activeTasks.filter(t => {
      const assigneeId = t.assignee || t.assignee_details?.[0]?.id || '';
      return String(assigneeId) === String(selectedMemberId);
    });
  }

  if (searchQuery) {
    const query = searchQuery.toLowerCase();
    activeTasks = activeTasks.filter(t => {
      const titleMatch   = (t.title || '').toLowerCase().includes(query);
      const assigneeName = t.assignee_details?.[0]?.name || '';
      const email        = t.assignee_details?.[0]?.email || '';
      return titleMatch || assigneeName.toLowerCase().includes(query) || email.toLowerCase().includes(query);
    });
  }

  // Group by priority for the task list
  const highTasks   = activeTasks.filter(t => (t.priority || '').toLowerCase() === 'high');
  const mediumTasks = activeTasks.filter(t => (t.priority || '').toLowerCase() === 'medium');
  const lowTasks    = activeTasks.filter(t => (t.priority || '').toLowerCase() === 'low');
  const otherTasks  = activeTasks.filter(t => {
    const p = (t.priority || '').toLowerCase();
    return p !== 'high' && p !== 'medium' && p !== 'low';
  });

  // ── Handlers ───────────────────────────────────────────────────────────────
  const handleAssigneeChange = async (taskId, userId) => {
    setAssigningTaskId(taskId);
    setError(null);
    setScheduleResult(null);
    try {
      await updateOrgTask(selectedOrg.slug, taskId, { assignees: userId ? [userId] : [] });
      await handleLoadTasks();
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.error || err.response?.data?.detail || 'Failed to update task assignment.');
    } finally {
      setAssigningTaskId(null);
    }
  };

  const handleRunManualSchedule = async () => {
    if (!selectedMemberId) {
      setError('Please select a workspace member to run scheduling for.');
      return;
    }
    setLoading(true);
    setError(null);
    setScheduleResult(null);
    try {
      const result = await manualScheduleTasks(selectedOrg.id, selectedMemberId);
      await handleLoadTasks();
      setScheduleResult(result); // show breakdown panel
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.error || err.response?.data?.detail || 'Failed to execute manual scheduling.');
    } finally {
      setLoading(false);
    }
  };

  // ── Interactive Builder Handlers ───────────────────────────────────────────
  const handlePreviewNewTask = () => {
    if (!newTaskTitle || !newTaskDuration) return;
    const durationMins = parseInt(newTaskDuration, 10) || 60;
    const slot = findEarliestAvailableSlot(localScheduleTasks, durationMins);
    setPreviewSchedule(slot);
  };

  const handleAddNewTask = () => {
    if (!newTaskTitle || !newTaskDuration) return;
    const durationMins = parseInt(newTaskDuration, 10) || 60;
    const slot = findEarliestAvailableSlot(localScheduleTasks, durationMins);
    
    const newTask = {
      id: 'local_' + Date.now(),
      title: newTaskTitle,
      startTime: slot.startTime,
      endTime: slot.endTime,
      memberId: newTaskMember,
    };
    
    setLocalScheduleTasks([...localScheduleTasks, newTask].sort((a, b) => parseTime(a.startTime) - parseTime(b.startTime)));
    setNewTaskTitle('');
    setNewTaskDuration('60');
    setPreviewSchedule(null);
  };

  const handleLocalTaskChange = (taskId, field, val) => {
    const updated = [...localScheduleTasks];
    const tIndex = updated.findIndex(t => t.id === taskId);
    if (tIndex === -1) return;
    
    if (field === 'startTime' || field === 'endTime') {
       // Trigger dynamic cascading reschedule on time change
       const task = updated[tIndex];
       const start = field === 'startTime' ? val : task.startTime;
       const end = field === 'endTime' ? val : task.endTime;
       
       if (parseTime(end) > parseTime(start)) {
         const shifted = rescheduleSubsequentTasks(updated, taskId, start, end);
         setLocalScheduleTasks(shifted);
       }
    } else {
       updated[tIndex] = { ...updated[tIndex], [field]: val };
       setLocalScheduleTasks(updated);
    }
  };

  // ── Sub-renders ────────────────────────────────────────────────────────────
  const renderTaskRow = (task) => {
    const currentAssigneeId = task.assignee || task.assignee_details?.[0]?.id || '';
    const estHours = task.estimated_hours
      ? `${parseFloat(task.estimated_hours).toFixed(1)}h`
      : task.estimated_minutes
        ? `${(task.estimated_minutes / 60).toFixed(1)}h`
        : '1h (default)';

    return (
      <div key={task.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.65rem 1rem', background: '#f8fafc', border: '1px solid #f1f5f9', borderRadius: '8px', marginBottom: '0.45rem', gap: '1rem' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#0f172a', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{task.title}</div>
          <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.1rem', display: 'flex', gap: '0.75rem' }}>
            <span>
              Status: <span style={{ textTransform: 'capitalize', fontWeight: 500, color: task.status === 'in_progress' ? '#3b82f6' : '#64748b' }}>{task.status?.replace('_', ' ')}</span>
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
              <Clock size={10} /> {estHours}
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
          <User size={13} style={{ color: '#94a3b8' }} />
          <select
            value={currentAssigneeId}
            disabled={assigningTaskId === task.id}
            onChange={(e) => handleAssigneeChange(task.id, e.target.value)}
            style={{ padding: '0.3rem 0.55rem', fontSize: '0.78rem', borderRadius: '6px', border: '1px solid #cbd5e1', backgroundColor: 'white', color: '#334155', cursor: 'pointer', outline: 'none' }}
          >
            <option value="">Unassigned</option>
            {orgMembers.map(m => {
              const userId = m.user?.id || m.user_id;
              const name   = m.user?.first_name || m.user?.last_name
                ? `${m.user.first_name || ''} ${m.user.last_name || ''}`.trim()
                : m.email;
              return <option key={userId} value={userId}>{name}</option>;
            })}
          </select>
        </div>
      </div>
    );
  };

  const renderSection = (title, taskList, color) => {
    if (taskList.length === 0) return null;
    return (
      <div style={{ marginBottom: '1.25rem' }}>
        <h4 style={{ margin: '0 0 0.6rem 0', fontSize: '0.8rem', fontWeight: 700, color, textTransform: 'uppercase', letterSpacing: '0.05em', display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
          <span style={{ width: '7px', height: '7px', borderRadius: '50%', backgroundColor: color, flexShrink: 0 }} />
          {title} ({taskList.length})
        </h4>
        {taskList.map(renderTaskRow)}
      </div>
    );
  };

  // ── Schedule Result Panel ──────────────────────────────────────────────────
  const renderScheduleResult = () => {
    if (!scheduleResult) return null;
    const { message, scheduled = [], unscheduled = [], scheduled_count, unscheduled_count } = scheduleResult;

    return (
      <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.1rem 1.25rem' }}>
        {/* Summary bar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <CheckCircle size={16} style={{ color: '#10b981', flexShrink: 0 }} />
          <span style={{ fontSize: '0.875rem', fontWeight: 600, color: '#047857' }}>{message}</span>
        </div>

        {/* Stats chips */}
        <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
          <span style={{ background: '#ecfdf5', color: '#065f46', border: '1px solid #6ee7b7', borderRadius: '20px', padding: '0.2rem 0.75rem', fontSize: '0.78rem', fontWeight: 600 }}>
            ✅ {scheduled_count} Scheduled
          </span>
          <span style={{ background: '#fff7ed', color: '#92400e', border: '1px solid #fdba74', borderRadius: '20px', padding: '0.2rem 0.75rem', fontSize: '0.78rem', fontWeight: 600 }}>
            ⏳ {unscheduled_count} Pending
          </span>
        </div>

        {/* Scheduled tasks */}
        {scheduled.length > 0 && (
          <div style={{ marginBottom: '1rem' }}>
            <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#10b981', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.5rem' }}>
              📅 Added to Calendar
            </div>
            {scheduled.map(t => (
              <div key={t.task_id} style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', padding: '0.55rem 0.75rem', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '7px', marginBottom: '0.4rem', gap: '0.75rem' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#0f172a' }}>{t.task_title}</div>
                  <div style={{ fontSize: '0.72rem', color: '#15803d', marginTop: '0.15rem' }}>
                    {t.scheduled_start_date} → {t.scheduled_due_date} &nbsp;·&nbsp; {t.estimated_hours}h estimated
                  </div>
                </div>
                <span style={{ background: '#bbf7d0', color: '#065f46', borderRadius: '4px', padding: '0.15rem 0.45rem', fontSize: '0.7rem', fontWeight: 700, flexShrink: 0, textTransform: 'capitalize' }}>
                  {t.priority}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Unscheduled tasks */}
        {unscheduled.length > 0 && (
          <div>
            <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#f97316', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.5rem' }}>
              ⚠️ Still Pending (no capacity in next 7 days)
            </div>
            {unscheduled.map(t => (
              <div key={t.task_id} style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', padding: '0.55rem 0.75rem', background: '#fff7ed', border: '1px solid #fed7aa', borderRadius: '7px', marginBottom: '0.4rem', gap: '0.75rem' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#0f172a' }}>{t.task_title}</div>
                  <div style={{ fontSize: '0.72rem', color: '#c2410c', marginTop: '0.15rem' }}>
                    {t.estimated_hours}h estimated &nbsp;·&nbsp; {t.message}
                  </div>
                </div>
                <span style={{ background: '#fed7aa', color: '#92400e', borderRadius: '4px', padding: '0.15rem 0.45rem', fontSize: '0.7rem', fontWeight: 700, flexShrink: 0, textTransform: 'capitalize' }}>
                  {t.priority}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(15, 23, 42, 0.45)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', backdropFilter: 'blur(4px)' }}>
      <div style={{ background: 'white', borderRadius: '16px', width: '780px', maxWidth: '95vw', minHeight: '600px', maxHeight: '88vh', display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.12), 0 8px 10px -6px rgba(0,0,0,0.1)' }}>

        {/* ── Header ── */}
        <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#ffffff', flexShrink: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
            <Calendar size={20} style={{ color: '#6366f1' }} />
            <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: '#0f172a' }}>Schedule Tasks</h3>
          </div>
          <button onClick={onClose} style={{ border: 'none', background: 'none', cursor: 'pointer', color: '#94a3b8', fontSize: '1.4rem', padding: 0, lineHeight: 1, display: 'flex' }}>×</button>
        </div>

        {/* ── Scrollable Content ── */}
        <div style={{ flex: 1, padding: '1.4rem 1.5rem', overflowY: 'auto', background: '#f8fafc', display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>

          {/* Error Alert */}
          {error && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#fef2f2', border: '1px solid #ef4444', color: '#b91c1c', padding: '0.7rem 1rem', borderRadius: '8px', fontSize: '0.83rem' }}>
              <AlertCircle size={15} />
              {error}
            </div>
          )}

          {/* ── Interactive Schedule Builder ── */}
          <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: '#1e293b', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Clock size={16} style={{ color: '#8b5cf6' }} /> Interactive Schedule Builder (No Overlaps)
            </h3>
            
            {/* Timeline Viewer */}
            <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid #cbd5e1', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', marginBottom: '0.2rem' }}>Current Timeline (Sorted by Start Time)</div>
              {localScheduleTasks.length === 0 && <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>No tasks in schedule.</div>}
              {localScheduleTasks.map(t => (
                <div key={t.id} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', background: 'white', padding: '0.5rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                  <input 
                    type="time" 
                    value={t.startTime} 
                    onChange={(e) => handleLocalTaskChange(t.id, 'startTime', e.target.value)}
                    style={{ padding: '0.2rem', fontSize: '0.8rem', border: '1px solid #cbd5e1', borderRadius: '4px', outline: 'none' }}
                  />
                  <span style={{ fontSize: '0.8rem', color: '#64748b' }}>to</span>
                  <input 
                    type="time" 
                    value={t.endTime} 
                    onChange={(e) => handleLocalTaskChange(t.id, 'endTime', e.target.value)}
                    style={{ padding: '0.2rem', fontSize: '0.8rem', border: '1px solid #cbd5e1', borderRadius: '4px', outline: 'none' }}
                  />
                  <input 
                    type="text" 
                    value={t.title} 
                    onChange={(e) => handleLocalTaskChange(t.id, 'title', e.target.value)}
                    style={{ flex: 1, padding: '0.3rem 0.5rem', fontSize: '0.85rem', border: '1px solid #cbd5e1', borderRadius: '4px', outline: 'none' }}
                  />
                </div>
              ))}
            </div>

            {/* Add New Task Form */}
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: '0.75rem', flexWrap: 'wrap' }}>
              <div style={{ flex: 1, minWidth: '150px' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>Task Title</label>
                <input 
                  type="text" 
                  placeholder="New task..."
                  value={newTaskTitle}
                  onChange={(e) => setNewTaskTitle(e.target.value)}
                  style={{ width: '100%', padding: '0.45rem', fontSize: '0.85rem', border: '1px solid #cbd5e1', borderRadius: '6px', outline: 'none' }}
                />
              </div>
              <div style={{ width: '120px' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>Duration (mins)</label>
                <input 
                  type="number" 
                  value={newTaskDuration}
                  onChange={(e) => setNewTaskDuration(e.target.value)}
                  style={{ width: '100%', padding: '0.45rem', fontSize: '0.85rem', border: '1px solid #cbd5e1', borderRadius: '6px', outline: 'none' }}
                />
              </div>
              <button 
                onClick={handlePreviewNewTask}
                style={{ padding: '0.5rem 1rem', fontSize: '0.85rem', fontWeight: 600, background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1', borderRadius: '6px', cursor: 'pointer' }}
              >
                Preview Slot
              </button>
              <button 
                onClick={handleAddNewTask}
                style={{ padding: '0.5rem 1rem', fontSize: '0.85rem', fontWeight: 600, background: '#8b5cf6', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
              >
                <PlusCircle size={15} /> Add Task
              </button>
            </div>

            {/* Preview Area */}
            {previewSchedule && (
              <div style={{ background: previewSchedule.isGapFilled ? '#f0fdfa' : '#fffbeb', border: `1px solid ${previewSchedule.isGapFilled ? '#99f6e4' : '#fde68a'}`, padding: '0.75rem', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle size={16} style={{ color: previewSchedule.isGapFilled ? '#0d9488' : '#d97706' }} />
                <span style={{ fontSize: '0.85rem', color: previewSchedule.isGapFilled ? '#0f766e' : '#b45309', fontWeight: 500 }}>
                  <strong>Schedule Preview:</strong> {previewSchedule.isGapFilled 
                    ? `Placed in available slot at ${formatTime(parseTime(previewSchedule.startTime))} - ${formatTime(parseTime(previewSchedule.endTime))}`
                    : `Appended after last task at ${formatTime(parseTime(previewSchedule.startTime))} - ${formatTime(parseTime(previewSchedule.endTime))}`
                  }
                </span>
              </div>
            )}
          </div>

          {/* ── Search / Filter Bar ── */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '0.7rem 1rem' }}>
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '8px', padding: '0 0.75rem' }}>
              <span style={{ fontSize: '0.85rem', color: '#94a3b8', marginRight: '0.45rem' }}>🔍</span>
              <input
                type="text"
                placeholder="Search tasks by title or assignee name…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{ width: '100%', border: 'none', background: 'transparent', padding: '0.45rem 0', fontSize: '0.83rem', color: '#1e293b', outline: 'none' }}
              />
              {searchQuery && (
                <button onClick={() => setSearchQuery('')} style={{ border: 'none', background: 'none', cursor: 'pointer', color: '#94a3b8', padding: '0 0.2rem', fontSize: '1rem' }}>×</button>
              )}
            </div>
            {selectedMemberId && (
              <button
                onClick={() => { setSelectedMemberId(''); setScheduleResult(null); }}
                style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '8px', padding: '0.45rem 0.8rem', fontSize: '0.78rem', color: '#475569', cursor: 'pointer', fontWeight: 600, whiteSpace: 'nowrap' }}
              >
                Clear Member Filter
              </button>
            )}
          </div>

          {/* ── Task List grouped by Priority ── */}
          <div style={{ flex: 1, background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.1rem 1.25rem', overflowY: 'auto' }}>
            <h3 style={{ margin: '0 0 0.9rem 0', fontSize: '0.9rem', fontWeight: 700, color: '#1e293b' }}>
              Active Tasks — Grouped by Priority
            </h3>

            {activeTasks.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '2.5rem 1rem', color: '#94a3b8', fontSize: '0.875rem' }}>
                No active tasks found in the workspace.
              </div>
            ) : (
              <>
                {renderSection('High Priority',   highTasks,   '#ef4444')}
                {renderSection('Medium Priority', mediumTasks, '#f97316')}
                {renderSection('Low Priority',    lowTasks,    '#3b82f6')}
                {renderSection('Other',           otherTasks,  '#64748b')}
              </>
            )}
          </div>

        </div>

        {/* ── Footer ── */}
        <div style={{ padding: '0.9rem 1.5rem', borderTop: '1px solid #e2e8f0', display: 'flex', justifyContent: 'flex-end', background: '#ffffff', flexShrink: 0 }}>
          <button onClick={onClose} style={{ width: 'auto', padding: '0.45rem 1.2rem', fontSize: '0.85rem', borderRadius: '8px', border: '1px solid #cbd5e1', background: '#f8fafc', color: '#334155', cursor: 'pointer', fontWeight: 600 }}>
            Close
          </button>
        </div>

        <style>{`
          @keyframes spin {
            0%   { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>

      </div>
    </div>
  );
}
