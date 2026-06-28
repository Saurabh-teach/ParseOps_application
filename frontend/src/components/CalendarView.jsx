import { useRef, useCallback, useState, useEffect, useMemo } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import resourceTimelinePlugin from '@fullcalendar/resource-timeline';
import api from '../api';
import { updateOrgTask, updateGoal } from '../api';

export default function WorkspaceCalendar({ selectedOrg, handleTaskClick, handleGoalClick }) {
  const calendarRef = useRef(null);
  const rawEventsRef = useRef([]);
  const dateRangeRef = useRef({ start: '', end: '' });

  // UI state for filters and color modes
  const [members, setMembers] = useState([]);
  const [selectedMember, setSelectedMember] = useState('');
  const [selectedPriority, setSelectedPriority] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [colorMode, setColorMode] = useState('priority'); // 'priority' | 'status' | 'assignee'

  // Fetch active organization members when organization changes
  useEffect(() => {
    if (!selectedOrg) {
      setMembers([]);
      return;
    }
    const fetchMembers = async () => {
      try {
        const response = await api.get(`/organizations/${selectedOrg.id}/members/`);
        setMembers(response.data || []);
      } catch (err) {
        console.error("Failed to fetch organization members:", err);
      }
    };
    fetchMembers();

    // Reset filters on org change
    setSelectedMember('');
    setSelectedPriority('');
    setSelectedStatus('');
  }, [selectedOrg]);

  // Generate resources for Timeline View
  const calendarResources = useMemo(() => {
    if (!members || members.length === 0) return [{ id: 'unassigned', title: 'Unassigned' }];
    const res = members.map(m => {
      const u = m.user || {};
      const name = `${u.first_name || ''} ${u.last_name || ''}`.trim() || m.email || u.email;
      return { id: String(m.user_id || m.id), title: name };
    });
    res.push({ id: 'unassigned', title: 'Unassigned' });
    return res;
  }, [members]);

  // Trigger FullCalendar refetch when filters or color mode changes
  useEffect(() => {
    if (calendarRef.current) {
      calendarRef.current.getApi().refetchEvents();
    }
  }, [selectedMember, selectedPriority, selectedStatus, colorMode]);

  // Helper to dynamically calculate color for each assignee
  const getAssigneeColor = (assigneeId) => {
    if (!assigneeId) {
      return { bg: '#f1f5f9', border: '#cbd5e1', text: '#475569' }; // Slate (unassigned)
    }
    let hash = 0;
    for (let i = 0; i < assigneeId.length; i++) {
      hash = assigneeId.charCodeAt(i) + ((hash << 5) - hash);
    }
    const hue = Math.abs(hash % 360);
    return {
      bg: `hsl(${hue}, 80%, 90%)`,
      border: `hsl(${hue}, 60%, 65%)`,
      text: `hsl(${hue}, 80%, 25%)`
    };
  };

  // Main event loader with caching and client-side filtering
  const fetchEvents = useCallback(async (fetchInfo, successCallback, failureCallback) => {
    if (!selectedOrg) {
      successCallback([]);
      return;
    }

    const startStr = fetchInfo.startStr;
    const endStr = fetchInfo.endStr;

    let eventsData = [];

    // Check if we can use cached raw events (range matches)
    if (
      dateRangeRef.current.start === startStr &&
      dateRangeRef.current.end === endStr &&
      rawEventsRef.current.length > 0
    ) {
      eventsData = [...rawEventsRef.current];
    } else {
      try {
        const response = await api.get(`/organizations/${selectedOrg.id}/calendar-events/`, {
          params: { start: startStr, end: endStr }
        });
        rawEventsRef.current = response.data || [];
        dateRangeRef.current = { start: startStr, end: endStr };
        eventsData = [...rawEventsRef.current];
      } catch (err) {
        console.error("Failed to fetch calendar events:", err);
        failureCallback(err);
        return;
      }
    }

    // Lookup table for selected member's email to filter leaves
    const selectedMemberEmail = selectedMember 
      ? members.find(m => m.user_id === selectedMember || m.id === selectedMember)?.email 
      : null;

    // Apply filters
    let filteredEvents = eventsData.filter(event => {
      const type = event.extendedProps?.type;

      if (type === 'task') {
        if (selectedMember && event.extendedProps.assignee_id !== selectedMember) return false;
        if (selectedPriority && event.extendedProps.priority !== selectedPriority) return false;
        if (selectedStatus && event.extendedProps.status !== selectedStatus) return false;
        return true;
      }

      if (type === 'leave') {
        // Leaves are only filtered by member, ignore priority/status filters
        if (selectedPriority || selectedStatus) return false;
        if (selectedMember && event.extendedProps.user !== selectedMemberEmail) return false;
        return true;
      }

      if (type === 'goal') {
        // Goals are hidden when filters are active to prevent clutter
        if (selectedMember || selectedPriority || selectedStatus) return false;
        return true;
      }

      return true;
    });

    // Apply color-coding mode dynamically
    filteredEvents = filteredEvents.map(event => {
      const type = event.extendedProps?.type;
      if (type !== 'task') return event; // Leaves and goals keep their backend-defined colors

      let bg = event.backgroundColor;
      let border = event.borderColor;
      let text = event.textColor || '#0f172a';

      if (colorMode === 'priority') {
        const p = event.extendedProps.priority;
        if (p === 'urgent' || p === 'high') { bg = '#ef4444'; border = '#dc2626'; text = '#ffffff'; }
        else if (p === 'medium') { bg = '#3b82f6'; border = '#2563eb'; text = '#ffffff'; }
        else { bg = '#22c55e'; border = '#16a34a'; text = '#ffffff'; }
      } else if (colorMode === 'status') {
        const s = event.extendedProps.status;
        if (s === 'backlog') { bg = '#94a3b8'; border = '#64748b'; text = '#ffffff'; }
        else if (s === 'todo') { bg = '#60a5fa'; border = '#3b82f6'; text = '#ffffff'; }
        else if (s === 'in_progress') { bg = '#f59e0b'; border = '#d97706'; text = '#ffffff'; }
        else if (s === 'in_review') { bg = '#a78bfa'; border = '#8b5cf6'; text = '#ffffff'; }
        else if (s === 'testing') { bg = '#22d3ee'; border = '#06b6d4'; text = '#ffffff'; }
        else { bg = '#10b981'; border = '#059669'; text = '#ffffff'; }
      } else if (colorMode === 'assignee') {
        const colors = getAssigneeColor(event.extendedProps.assignee_id);
        bg = colors.bg;
        border = colors.border;
        text = colors.text;
      }

      return {
        ...event,
        resourceId: event.extendedProps?.assignee_id ? String(event.extendedProps.assignee_id) : 'unassigned',
        backgroundColor: bg,
        borderColor: border,
        textColor: text
      };
    });

    successCallback(filteredEvents);
  }, [selectedOrg, selectedMember, selectedPriority, selectedStatus, colorMode, members]);

  // Reschedule via drag & drop (preserves exact time details)
  const handleEventDrop = async (dropInfo) => {
    const { event } = dropInfo;
    const type = event.extendedProps.type;
    const originalId = event.extendedProps.original_id;

    try {
      if (type === 'task') {
        const payload = {
          planned_start: event.start ? event.start.toISOString() : null,
          planned_end: event.end ? event.end.toISOString() : (event.start ? event.start.toISOString() : null),
          is_auto_scheduled: false
        };
        await updateOrgTask(selectedOrg.slug, originalId, payload);
        // Force refetch to ensure cascading updates display correctly
        rawEventsRef.current = [];
        if (calendarRef.current) calendarRef.current.getApi().refetchEvents();
      } else if (type === 'goal') {
        const startDate = event.start ? event.start.toISOString().split('T')[0] : null;
        let endDate = event.end ? event.end.toISOString().split('T')[0] : startDate;
        if (event.allDay && event.end) {
          const d = new Date(event.end);
          d.setDate(d.getDate() - 1);
          endDate = d.toISOString().split('T')[0];
        }
        await updateGoal(originalId, {
          end_date: endDate,
          start_date: startDate
        });
      }
    } catch (err) {
      console.error("Failed to update event date:", err);
      dropInfo.revert();
      alert("Failed to reschedule event. Make sure you have permission.");
    }
  };

  // Reschedule via resizing (preserves exact time details)
  const handleEventResize = async (resizeInfo) => {
    const { event } = resizeInfo;
    const type = event.extendedProps.type;
    const originalId = event.extendedProps.original_id;

    try {
      if (type === 'task') {
        const payload = {
          planned_start: event.start ? event.start.toISOString() : null,
          planned_end: event.end ? event.end.toISOString() : null,
          is_auto_scheduled: false
        };
        await updateOrgTask(selectedOrg.slug, originalId, payload);
        // Force refetch to ensure cascading updates display correctly
        rawEventsRef.current = [];
        if (calendarRef.current) calendarRef.current.getApi().refetchEvents();
      } else if (type === 'goal') {
        let endDate = event.end ? event.end.toISOString().split('T')[0] : null;
        if (event.allDay && event.end) {
          const d = new Date(event.end);
          d.setDate(d.getDate() - 1);
          endDate = d.toISOString().split('T')[0];
        }
        await updateGoal(originalId, { end_date: endDate });
      }
    } catch (err) {
      console.error("Failed to update event date:", err);
      resizeInfo.revert();
      alert("Failed to reschedule event.");
    }
  };

  const handleEventClick = (clickInfo) => {
    const { event } = clickInfo;
    const type = event.extendedProps.type;
    const originalId = event.extendedProps.original_id;

    if (type === 'task') {
      if (handleTaskClick) handleTaskClick(originalId);
    } else if (type === 'goal') {
      if (handleGoalClick) handleGoalClick(originalId);
    }
  };

  // Custom multiline card event renderer
  const renderEventContent = (eventInfo) => {
    const { event } = eventInfo;
    const type = event.extendedProps.type;
    const priority = event.extendedProps.priority;
    const status = event.extendedProps.status;
    const assigneeName = event.extendedProps.assignee_name;
    const estHours = event.extendedProps.estimated_hours;

    const displayTitle = event.title.replace(/^\[Task\]\s*|^\[Goal\]\s*|^\[On Leave\]\s*/i, '');

    return (
      <div 
        className="fc-event-custom-container"
        style={{
          display: 'flex',
          flexDirection: 'column',
          width: '100%',
          overflow: 'hidden',
          fontSize: '0.78rem',
          lineHeight: '1.25',
          padding: '4px 6px',
          borderRadius: '6px',
          boxSizing: 'border-box'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontWeight: '600', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
            {displayTitle}
          </span>
          {estHours > 0 && (
            <span style={{ fontSize: '0.65rem', opacity: 0.8, fontWeight: 'normal', marginLeft: '4px' }}>
              {estHours}h
            </span>
          )}
        </div>
        
        {type === 'task' && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-start', marginTop: '4px', fontSize: '0.68rem', opacity: 0.95 }}>
            <span style={{ 
              padding: '1px 4px', 
              borderRadius: '4px', 
              fontSize: '0.62rem', 
              textTransform: 'uppercase',
              backgroundColor: 'rgba(255, 255, 255, 0.45)',
              fontWeight: '700',
              border: '1px solid rgba(0, 0, 0, 0.08)'
            }}>
              {status}
            </span>
          </div>
        )}
      </div>
    );
  };

  return (
    <div style={{ 
      height: '100%', 
      minHeight: '680px', 
      backgroundColor: '#fff', 
      padding: '1.25rem', 
      borderRadius: '16px', 
      boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.05), 0 4px 6px -4px rgb(0 0 0 / 0.05)',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Controls & Filters Bar */}
      <div style={{ 
        display: 'flex', 
        flexWrap: 'wrap', 
        gap: '16px', 
        alignItems: 'center', 
        justifyContent: 'space-between', 
        marginBottom: '16px', 
        paddingBottom: '16px', 
        borderBottom: '1px solid #f1f5f9' 
      }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '14px', alignItems: 'center' }}>
          {/* Member Dropdown */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label style={{ fontSize: '0.72rem', fontWeight: '700', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Assignee</label>
            <select 
              value={selectedMember} 
              onChange={(e) => setSelectedMember(e.target.value)}
              style={{ 
                padding: '6px 12px', 
                borderRadius: '8px', 
                border: '1px solid #cbd5e1', 
                fontSize: '0.85rem', 
                backgroundColor: '#fff', 
                outline: 'none', 
                minWidth: '160px',
                color: '#334155',
                cursor: 'pointer',
                transition: 'border-color 0.15s ease'
              }}
            >
              <option value="">All Members</option>
              {members.map(m => (
                <option key={m.id} value={m.user_id}>
                  {m.user?.first_name || m.user?.last_name 
                    ? `${m.user.first_name} ${m.user.last_name}`.trim() 
                    : m.email}
                </option>
              ))}
            </select>
          </div>

          {/* Priority Dropdown */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label style={{ fontSize: '0.72rem', fontWeight: '700', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Priority</label>
            <select 
              value={selectedPriority} 
              onChange={(e) => setSelectedPriority(e.target.value)}
              style={{ 
                padding: '6px 12px', 
                borderRadius: '8px', 
                border: '1px solid #cbd5e1', 
                fontSize: '0.85rem', 
                backgroundColor: '#fff', 
                outline: 'none',
                color: '#334155',
                cursor: 'pointer'
              }}
            >
              <option value="">All Priorities</option>
              <option value="urgent">Urgent</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          {/* Status Dropdown */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label style={{ fontSize: '0.72rem', fontWeight: '700', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Status</label>
            <select 
              value={selectedStatus} 
              onChange={(e) => setSelectedStatus(e.target.value)}
              style={{ 
                padding: '6px 12px', 
                borderRadius: '8px', 
                border: '1px solid #cbd5e1', 
                fontSize: '0.85rem', 
                backgroundColor: '#fff', 
                outline: 'none',
                color: '#334155',
                cursor: 'pointer'
              }}
            >
              <option value="">All Statuses</option>
              <option value="backlog">Backlog</option>
              <option value="todo">Todo</option>
              <option value="in_progress">In Progress</option>
              <option value="in_review">In Review</option>
              <option value="testing">Testing</option>
              <option value="done">Done</option>
            </select>
          </div>
        </div>

        {/* Color Code Selector */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <label style={{ fontSize: '0.72rem', fontWeight: '700', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Color Coding Mode</label>
          <select 
            value={colorMode} 
            onChange={(e) => setColorMode(e.target.value)}
            style={{ 
              padding: '6px 12px', 
              borderRadius: '8px', 
              border: '1px solid #cbd5e1', 
              fontSize: '0.85rem', 
              backgroundColor: '#fff', 
              outline: 'none',
              fontWeight: '600',
              color: '#1e293b',
              cursor: 'pointer'
            }}
          >
            <option value="priority">Color by Priority</option>
            <option value="status">Color by Status</option>
            <option value="assignee">Color by Assignee</option>
          </select>
        </div>
      </div>

      {/* Legend Container */}
      <div style={{ 
        display: 'flex', 
        flexWrap: 'wrap', 
        gap: '12px', 
        fontSize: '0.75rem', 
        color: '#475569', 
        marginBottom: '16px', 
        padding: '10px 14px', 
        backgroundColor: '#f8fafc', 
        borderRadius: '10px',
        alignItems: 'center',
        border: '1px solid #e2e8f0'
      }}>
        <span style={{ fontWeight: '700', color: '#64748b', textTransform: 'uppercase', fontSize: '0.68rem', letterSpacing: '0.05em' }}>Legend:</span>
        {colorMode === 'priority' && (
          <>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontWeight: '500' }}>
              <span style={{ width: '12px', height: '12px', borderRadius: '4px', backgroundColor: '#ef4444', border: '1px solid #dc2626' }}></span> High
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontWeight: '500' }}>
              <span style={{ width: '12px', height: '12px', borderRadius: '4px', backgroundColor: '#3b82f6', border: '1px solid #2563eb' }}></span> Medium
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontWeight: '500' }}>
              <span style={{ width: '12px', height: '12px', borderRadius: '4px', backgroundColor: '#22c55e', border: '1px solid #16a34a' }}></span> Low
            </span>
          </>
        )}
        {colorMode === 'status' && (
          <>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontWeight: '500' }}>
              <span style={{ width: '12px', height: '12px', borderRadius: '4px', backgroundColor: '#94a3b8', border: '1px solid #64748b' }}></span> Backlog
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontWeight: '500' }}>
              <span style={{ width: '12px', height: '12px', borderRadius: '4px', backgroundColor: '#60a5fa', border: '1px solid #3b82f6' }}></span> Todo
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontWeight: '500' }}>
              <span style={{ width: '12px', height: '12px', borderRadius: '4px', backgroundColor: '#f59e0b', border: '1px solid #d97706' }}></span> In Progress
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontWeight: '500' }}>
              <span style={{ width: '12px', height: '12px', borderRadius: '4px', backgroundColor: '#a78bfa', border: '1px solid #8b5cf6' }}></span> In Review
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontWeight: '500' }}>
              <span style={{ width: '12px', height: '12px', borderRadius: '4px', backgroundColor: '#22d3ee', border: '1px solid #06b6d4' }}></span> Testing
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontWeight: '500' }}>
              <span style={{ width: '12px', height: '12px', borderRadius: '4px', backgroundColor: '#10b981', border: '1px solid #059669' }}></span> Done
            </span>
          </>
        )}
        {colorMode === 'assignee' && (
          <span style={{ fontStyle: 'italic', color: '#64748b', fontSize: '0.72rem' }}>Tasks dynamically assigned unique colors per member.</span>
        )}
        <span style={{ width: '1px', height: '12px', backgroundColor: '#cbd5e1', margin: '0 6px' }}></span>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontWeight: '500' }}>
          <span style={{ width: '12px', height: '12px', borderRadius: '4px', backgroundColor: '#c084fc', border: '1px solid #a855f7' }}></span> Goal
        </span>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontWeight: '500' }}>
          <span style={{ width: '12px', height: '12px', borderRadius: '4px', backgroundColor: '#f87171', border: '1px solid #ef4444' }}></span> Approved Leave
        </span>
      </div>

      {/* FullCalendar Wrapper */}
      <div style={{ flex: 1, position: 'relative' }}>
        <FullCalendar
          ref={calendarRef}
          plugins={[ dayGridPlugin, timeGridPlugin, interactionPlugin, resourceTimelinePlugin ]}
          initialView="resourceTimelineWeek"
          resources={calendarResources}
          resourceAreaWidth="20%"
          resourceAreaHeaderContent="Members"
          headerToolbar={{
            left: 'prev,next today',
            center: 'title',
            right: 'resourceTimelineMonth,resourceTimelineWeek,resourceTimelineDay'
          }}
          events={fetchEvents}
          editable={true}
          droppable={true}
          eventDrop={handleEventDrop}
          eventResize={handleEventResize}
          eventClick={handleEventClick}
          eventContent={renderEventContent}
          height="100%"
          themeSystem="standard"
          dayMaxEvents={3} // Collapse overlapping elements gracefully
          eventMinHeight={26}
          slotEventOverlap={false} // Side-by-side rather than overlapping columns in time grid
          nowIndicator={true}
        />
      </div>
    </div>
  );
}
