import React, { useState, useEffect, useRef } from 'react';
import { handleTimeFieldChange as scheduleHandleTimeFieldChange, toDatetimeLocal as scheduleToDatetimeLocal, calcWorkEndTime } from './utils/scheduleUtils';
import WorkspaceCalendar from './components/CalendarView';
import ContextualChat from './components/Chat/ContextualChat';
import TemplateManager from './components/Templates/TemplateManager';
import PendingQueueView from './components/PendingQueueView';
import CheckFreeMembersModal from './components/CheckFreeMembersModal';
import NotificationDropdown from './components/NotificationDropdown';
import {
  Mail, Lock, Eye, EyeOff, AudioWaveform, Loader2, LogOut,
  User as UserIcon, Key, CheckCircle2, ArrowLeft, RefreshCw,
  LayoutDashboard, ListTodo, FileText, Settings, Bell, Search, BarChart2,
  Plus, Users, MessageSquare, Briefcase, ChevronRight, Hash,
  Calendar, Clock, History, Edit3, Trash2, StickyNote, BookOpen, Target, Coffee,
  Filter, AlertCircle, Grid, List, Inbox, ArrowRight, MoreVertical, Repeat, Paperclip, X, Folder, Archive, Hourglass, Award
} from 'lucide-react';
import {
  loginRequest,
  verifyLoginOTP,
  registerRequest,
  verifyRegistrationOTP,
  resendLoginOTP,
  resendRegistrationOTP,
  logout,
  setAuthTokens,
  forgotPasswordRequest,
  resetPasswordVerify,
  changePassword,
  getUserProfile,
  updateUserProfile,
  requestEmailChange,
  verifyEmailChange,
  getOrganizations,
  getMyWorkspaces,
  createOrganization,
  sendJoinRequest,
  getOrganizationMembers,
  inviteMember,
  getJoinRequests,
  manageJoinRequest,
  getWorkspaceHistory,
  getPendingInvitations,
  cancelInvitation,
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  acceptInvitation,
  declineInvitation,
  updateOrganization,
  deleteOrganization,
  deactivateOrganization,
  reactivateOrganization,
  removeMember,
  changeMemberRole,
  getNotes,
  createNote,
  updateNote,
  deleteNote,
  restoreMember,
  restoreNote,
  getGoals,
  createGoal,
  getGoalDetail,
  updateGoal,
  deleteGoal,
  restoreGoal,
  getKeyResults,
  createKeyResult,
  updateKeyResult,
  deleteKeyResult,
  getTasks,
  createTask,
  getTaskDetail,
  updateTask,
  updateTaskStatus,
  deleteTask,
  getTaskComments,
  createTaskComment,
  updateTaskComment,
  deleteTaskComment,
  replyToComment,
  getOrgGoals,
  createOrgGoal,
  applyTemplateToGoal,
  getOrgGoalDetail,
  updateOrgGoal,
  deleteOrgGoal,
  getOrgTasks,
  createOrgTask,
  getOrgTaskDetail,
  updateOrgTask,
  deleteOrgTask,
  getTasksKanban,
  updateTaskTicketStatus,
  submitTaskProof,
  saveWebPushSubscription,
  importCSV,
  applyLeave,
  getUserLeaves,
  getAllLeaves,
  approveLeave,
  rejectLeave,
  cancelLeave,
  getLeaveBalances,
  getSmartSuggest,
  checkFreeMembers,
  manualScheduleTasks,
  schedulePreview as getSchedulePreviewApi,
  getExtensionRequests,
  runScheduler,
  importTasksCSV,
  baseURL,
  default as api
} from './api';
import Dashboard from './components/Dashboard';
import TaskFeedbackModal from './components/TaskFeedbackModal';
import TaskExtensionModal from './components/TaskExtensionModal';
import ExtensionRequestsModal from './components/ExtensionRequestsModal';

import ChatLayout from './components/Chat/ChatLayout';
import { useModal } from './context/ModalContext';



function TicketTimer({ ticket, totalEstimatedMinutes, numAssignees }) {
  const getBaseSeconds = () => {
    if (Number.isFinite(ticket.total_elapsed_seconds)) {
      return ticket.total_elapsed_seconds;
    }
    return (ticket.time_spent_minutes || 0) * 60;
  };
  const getTimerStartMs = () => {
    const startedAt = ticket.timer_started_at || ticket.updated_at;
    return startedAt ? new Date(startedAt).getTime() : null;
  };
  const [elapsedSeconds, setElapsedSeconds] = useState(getBaseSeconds);
  useEffect(() => {
    let interval = null;
    const savedSeconds = (ticket.time_spent_minutes || 0) * 60;
    const apiRunningSeconds = ticket.running_elapsed_seconds || 0;
    const apiTotalSeconds = Number.isFinite(ticket.total_elapsed_seconds)
      ? ticket.total_elapsed_seconds
      : savedSeconds + apiRunningSeconds;
    const timerStartMs = getTimerStartMs();
    if (ticket.status === 'in_progress') {
      const update = () => {
        if (timerStartMs) {
          const liveRunningSeconds = Math.max(0, Math.floor((Date.now() - timerStartMs) / 1000));
          setElapsedSeconds(savedSeconds + liveRunningSeconds);
        } else {
          setElapsedSeconds(prev => Math.max(prev, apiTotalSeconds) + 1);
        }
      };
      update();
      interval = setInterval(update, 1000);
    } else {
      setElapsedSeconds(savedSeconds);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [
    ticket.status,
    ticket.updated_at,
    ticket.timer_started_at,
    ticket.time_spent_minutes,
    ticket.running_elapsed_seconds,
    ticket.total_elapsed_seconds
  ]);
  const assignedMinutes = totalEstimatedMinutes ? Math.floor(totalEstimatedMinutes / (numAssignees || 1)) : 0;
  const savedMinutes = ticket.time_spent_minutes || 0;
  const savedH = Math.floor(savedMinutes / 60);
  const savedM = savedMinutes % 60;
  // Format elapsed time (hours and minutes)
  const totalSpentMinutes = Math.floor(elapsedSeconds / 60);
  const spentH = Math.floor(totalSpentMinutes / 60);
  const spentM = totalSpentMinutes % 60;
  const runningS = elapsedSeconds % 60;
  // Format estimated time
  const estH = Math.floor(assignedMinutes / 60);
  const estM = assignedMinutes % 60;
  // Format remaining time
  const remainingMinutes = assignedMinutes - totalSpentMinutes;
  const isOverTime = remainingMinutes < 0;
  const absRemMinutes = Math.abs(remainingMinutes);
  const remH = Math.floor(absRemMinutes / 60);
  const remM = absRemMinutes % 60;
  // Status text
  let statusText = "Paused";
  let statusColor = "#64748b"; // slate
  if (ticket.status === 'in_progress') {
    statusText = "Running";
    statusColor = "#ea580c"; // orange
  } else if (ticket.status === 'done') {
    statusText = "Completed";
    statusColor = "#10b981"; // green
  }
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '0.35rem',
      fontSize: '0.75rem',
      fontWeight: 600,
      color: statusColor,
      marginTop: '0.2rem'
    }}>
      <Clock
        size={12}
        style={ticket.status === 'in_progress' ? { animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite', color: statusColor } : { color: statusColor }}
      />
      <span>{statusText}: {spentH}h {spentM}m</span>
      <span style={{ margin: '0 0.15rem', color: '#cbd5e1' }}>|</span>
      <span>Assigned: {estH}h {estM}m</span>
    </div>
  );
}
// Slim sidebar icon button with tooltip
function SlimNavItem({ icon, label, active, onClick, badge }) {
  return (
    <div className={`slim-nav-item ${active ? 'active' : ''}`} onClick={onClick} title={label}>
      <div className="slim-icon-wrap">
        {icon}
        {badge > 0 && <span className="slim-badge">{badge}</span>}
      </div>
      <span className="slim-tooltip">{label}</span>
    </div>
  );
}
function SharingSettingsModal({ isOpen, onClose, data, onChange, members }) {
  const [activeTab, setActiveTab] = useState('option');
  if (!isOpen) return null;
  const handleOptionChange = (opt) => {
    onChange({ ...data, sharing_option: opt });
    if (opt !== 'specific') {
      onChange({ ...data, sharing_option: opt, shared_viewers: [] }); // reset viewers
    }
  };
  const toggleAssignee = (id) => {
    const current = data.assignees || [];
    if (current.includes(id)) {
      onChange({ ...data, assignees: current.filter(x => x !== id) });
    } else {
      if (current.length >= 1) {
        alert("Warning: You cannot assign multiple members. A task can only have one unique member.");
        return;
      }
      onChange({ ...data, assignees: [...current, id] });
    }
  };
  const toggleViewer = (id) => {
    const current = data.shared_viewers || [];
    if (current.includes(id)) {
      onChange({ ...data, shared_viewers: current.filter(x => x !== id) });
    } else {
      onChange({ ...data, shared_viewers: [...current, id] });
    }
  };
  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(15, 23, 42, 0.4)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', backdropFilter: 'blur(4px)' }}>
      <div style={{ background: 'white', borderRadius: '16px', width: '650px', maxWidth: '95vw', height: '450px', display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.1)' }}>
        <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#ffffff' }}>
          <h3 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 600, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Users size={20} style={{ color: '#6366f1' }} /> Sharing & Permissions
          </h3>
          <button onClick={onClose} style={{ border: 'none', background: 'none', cursor: 'pointer', color: '#94a3b8', fontSize: '1.5rem', padding: 0, lineHeight: 1, display: 'flex' }} onMouseEnter={(e) => e.target.style.color = '#334155'} onMouseLeave={(e) => e.target.style.color = '#94a3b8'}>&times;</button>
        </div>
        <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          <div style={{ width: '200px', borderRight: '1px solid #e2e8f0', background: '#f8fafc', display: 'flex', flexDirection: 'column', padding: '1rem 0' }}>
            <button
              onClick={() => setActiveTab('option')}
              style={{ padding: '0.85rem 1.5rem', textAlign: 'left', border: 'none', background: activeTab === 'option' ? '#eef2ff' : 'transparent', color: activeTab === 'option' ? '#4f46e5' : '#64748b', fontWeight: activeTab === 'option' ? 600 : 500, cursor: 'pointer', borderRight: activeTab === 'option' ? '3px solid #4f46e5' : '3px solid transparent', display: 'flex', alignItems: 'center', gap: '0.5rem', transition: 'all 0.2s' }}
            >
              <Target size={16} /> Access Level
            </button>
            <button
              onClick={() => setActiveTab('assignees')}
              style={{ padding: '0.85rem 1.5rem', textAlign: 'left', border: 'none', background: activeTab === 'assignees' ? '#eef2ff' : 'transparent', color: activeTab === 'assignees' ? '#4f46e5' : '#64748b', fontWeight: activeTab === 'assignees' ? 600 : 500, cursor: 'pointer', borderRight: activeTab === 'assignees' ? '3px solid #4f46e5' : '3px solid transparent', display: 'flex', alignItems: 'center', gap: '0.5rem', transition: 'all 0.2s' }}
            >
              <UserIcon size={16} /> Assignees
            </button>
            <button
              onClick={() => setActiveTab('viewers')}
              disabled={data.sharing_option !== 'specific'}
              style={{ padding: '0.85rem 1.5rem', textAlign: 'left', border: 'none', background: activeTab === 'viewers' ? '#eef2ff' : 'transparent', color: data.sharing_option !== 'specific' ? '#cbd5e1' : (activeTab === 'viewers' ? '#4f46e5' : '#64748b'), fontWeight: activeTab === 'viewers' ? 600 : 500, cursor: data.sharing_option !== 'specific' ? 'not-allowed' : 'pointer', borderRight: activeTab === 'viewers' ? '3px solid #4f46e5' : '3px solid transparent', display: 'flex', alignItems: 'center', gap: '0.5rem', transition: 'all 0.2s' }}
              title={data.sharing_option !== 'specific' ? "Only available when 'Specific People' is selected" : ""}
            >
              <Eye size={16} /> Shared Viewers
            </button>
          </div>
          <div style={{ flex: 1, padding: '1.5rem', overflowY: 'auto', background: 'white' }}>
            {activeTab === 'option' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '1rem', color: '#1e293b' }}>Select Access Level</h4>
                {[
                  { id: 'organization', title: 'Entire Workspace', desc: 'Anyone in the organization can view this.' },
                  { id: 'private', title: 'Private', desc: 'Only assignees and the creator can view.' },
                  { id: 'specific', title: 'Specific People', desc: 'Choose exactly who has read-only access.' }
                ].map(opt => (
                  <label key={opt.id} style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem', padding: '1rem', border: data.sharing_option === opt.id ? '2px solid #6366f1' : '1px solid #e2e8f0', borderRadius: '10px', cursor: 'pointer', background: data.sharing_option === opt.id ? '#f5f7ff' : 'white', transition: 'all 0.2s' }}>
                    <input type="radio" checked={data.sharing_option === opt.id} onChange={() => handleOptionChange(opt.id)} style={{ marginTop: '0.25rem', accentColor: '#6366f1', width: '16px', height: '16px', cursor: 'pointer' }} />
                    <div>
                      <div style={{ fontWeight: 600, color: '#0f172a', marginBottom: '0.25rem' }}>{opt.title}</div>
                      <div style={{ fontSize: '0.875rem', color: '#64748b', lineHeight: 1.4 }}>{opt.desc}</div>
                    </div>
                  </label>
                ))}
              </div>
            )}
            {activeTab === 'assignees' && (
              <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                <div style={{ marginBottom: '1rem' }}>
                  <h4 style={{ margin: 0, fontSize: '1rem', color: '#1e293b' }}>Select Assignees</h4>
                  <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.85rem', color: '#64748b' }}>Users who can edit and comment on this item.</p>
                </div>
                <div style={{ flex: 1, overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '10px', background: 'white' }}>
                  {members.map((m, idx) => (
                    <label key={m.id} style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.85rem 1rem', cursor: 'pointer', borderBottom: idx < members.length - 1 ? '1px solid #f1f5f9' : 'none', margin: 0, background: (data.assignees || []).includes(m.user_id) ? '#fafafa' : 'white', transition: 'background 0.2s' }} onMouseEnter={(e) => { if (!(data.assignees || []).includes(m.user_id)) e.currentTarget.style.background = '#f8fafc' }} onMouseLeave={(e) => { if (!(data.assignees || []).includes(m.user_id)) e.currentTarget.style.background = 'white' }}>
                      <input type="checkbox" checked={(data.assignees || []).includes(m.user_id)} onChange={() => toggleAssignee(m.user_id)} style={{ accentColor: '#6366f1', width: '16px', height: '16px', cursor: 'pointer' }} />
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: '#e0e7ff', color: '#4f46e5', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 600 }}>{m.email[0].toUpperCase()}</div>
                        <span style={{ fontSize: '0.9rem', fontWeight: 500, color: '#334155', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                          {m.email}
                          {m.is_on_leave && (
                            <span style={{ backgroundColor: '#fee2e2', color: '#b91c1c', padding: '0.1rem 0.35rem', borderRadius: '4px', fontSize: '0.65rem', fontWeight: 'bold' }}>On Leave</span>
                          )}
                        </span>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            )}
            {activeTab === 'viewers' && (
              <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                <div style={{ marginBottom: '1rem' }}>
                  <h4 style={{ margin: 0, fontSize: '1rem', color: '#1e293b' }}>Select Shared Viewers</h4>
                  <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.85rem', color: '#64748b' }}>Users who have read-only access to this item.</p>
                </div>
                <div style={{ flex: 1, overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '10px', background: 'white' }}>
                  {members.map((m, idx) => (
                    <label key={m.id} style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.85rem 1rem', cursor: 'pointer', borderBottom: idx < members.length - 1 ? '1px solid #f1f5f9' : 'none', margin: 0, background: (data.shared_viewers || []).includes(m.user_id) ? '#fafafa' : 'white', transition: 'background 0.2s' }} onMouseEnter={(e) => { if (!(data.shared_viewers || []).includes(m.user_id)) e.currentTarget.style.background = '#f8fafc' }} onMouseLeave={(e) => { if (!(data.shared_viewers || []).includes(m.user_id)) e.currentTarget.style.background = 'white' }}>
                      <input type="checkbox" checked={(data.shared_viewers || []).includes(m.user_id)} onChange={() => toggleViewer(m.user_id)} style={{ accentColor: '#6366f1', width: '16px', height: '16px', cursor: 'pointer' }} />
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: '#f1f5f9', color: '#64748b', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 600 }}>{m.email[0].toUpperCase()}</div>
                        <span style={{ fontSize: '0.9rem', fontWeight: 500, color: '#334155' }}>{m.email}</span>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
        <div style={{ padding: '1rem 1.5rem', borderTop: '1px solid #e2e8f0', display: 'flex', justifyContent: 'flex-end', background: '#ffffff' }}>
          <button onClick={onClose} style={{ background: '#6366f1', color: 'white', border: 'none', padding: '0.6rem 2rem', borderRadius: '8px', fontWeight: 600, cursor: 'pointer', boxShadow: '0 2px 4px rgba(99, 102, 241, 0.2)', transition: 'background 0.2s' }} onMouseEnter={(e) => e.target.style.background = '#4f46e5'} onMouseLeave={(e) => e.target.style.background = '#6366f1'}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
}

function formatTaskCreateSuccess(response) {
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
    ].join('\n');
  }
  if (task.planned_start && task.planned_end && task.schedule_status === 'SCHEDULED') {
    const startDate = new Date(task.planned_start);
    const endDate = new Date(task.planned_end);
    const dateStr = startDate.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
    const startStr = startDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
    const endStr = endDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
    return [
      'Task created successfully!',
      '',
      `Scheduled Date: ${dateStr}`,
      `Start Time: ${startStr}`,
      `End Time: ${endStr}`,
      'Status: SCHEDULED',
    ].join('\n');
  }
  return [
    'Task created successfully!',
    '',
    'Status: QUEUED',
    'No available slot found within the next 7 working days. Task is QUEUED.',
  ].join('\n');
}

const toDatetimeLocal = (isoString) => {
  if (!isoString) return '';
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return '';
    const localSV = d.toLocaleString('sv', { timeZoneName: undefined });
    return localSV.substring(0, 16).replace(' ', 'T');
  } catch (e) {
    return '';
  }
};

function App() {
  const modal = useModal();
  const [taskDetailTab, setTaskDetailTab] = useState('details');
  const [goalDetailTab, setGoalDetailTab] = useState('details');
  const [view, setView] = useState(sessionStorage.getItem('access_token') ? 'initializing' : 'login');
  const [purpose, setPurpose] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [workloadLimitWarning, setWorkloadLimitWarning] = useState(null);
  const [message, setMessage] = useState('');
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const otpRefs = useRef([]);

  // Workspace States
  const [organizations, setOrganizations] = useState([]);
  const [selectedRoles, setSelectedRoles] = useState({});
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedTemplateId, setSelectedTemplateId] = useState(null);
  const [newOrgData, setNewOrgData] = useState({ name: '', description: '', useCase: '', initialInvites: '' });
  const [createOrgStep, setCreateOrgStep] = useState(1);
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [joinOrgId, setJoinOrgId] = useState(null);
  const [joinMessage, setJoinMessage] = useState('');
  const [collaborateOrg, setCollaborateOrg] = useState(null);
  const [selectedOrg, setSelectedOrg] = useState(null);
  const [orgMembers, setOrgMembers] = useState([]);
  const [joinRequests, setJoinRequests] = useState([]);
  const [workspaceApps, setWorkspaceApps] = useState([]);
  const [pushToast, setPushToast] = useState(null);

  useEffect(() => {
    const handleWorkspaceLost = () => {
      setSelectedOrg(null);
      sessionStorage.removeItem('selectedOrgId');
      setView('onboarding');
      console.warn('Workspace access lost event received.');
      getOrganizations().then(orgs => setOrganizations(orgs)).catch(() => { });
    };
    window.addEventListener('workspace_access_lost', handleWorkspaceLost);

    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('message', (event) => {
        if (event.data && event.data.type === 'PUSH_NOTIFICATION') {
          setPushToast({ title: event.data.title, body: event.data.body });
          setTimeout(() => setPushToast(null), 6000);
        }
      });
    }
    return () => window.removeEventListener('workspace_access_lost', handleWorkspaceLost);
  }, []);

  const [activeTabState, setActiveTabState] = useState(sessionStorage.getItem('activeTab') || 'overview');
  const [initialChatRoomId, setInitialChatRoomId] = useState(null);
  const activeTab = activeTabState;
  const setActiveTab = (tab) => {
    sessionStorage.setItem('activeTab', tab);
    setActiveTabState(tab);
  };
  const [showNotifications, setShowNotifications] = useState(false);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [confirmInput, setConfirmInput] = useState('');
  const [confirmModalError, setConfirmModalError] = useState('');
  const [inviteData, setInviteData] = useState({ email: '', role: 'member', message: '' });
  const [pendingInvites, setPendingInvites] = useState([]);
  const [showRoleDropdown, setShowRoleDropdown] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [isLoggedIn, setIsLoggedIn] = useState(!!sessionStorage.getItem('access_token'));
  const [mustChangePassword, setMustChangePassword] = useState(sessionStorage.getItem('mustChangePassword') === 'true');
  // Sharing Settings Modal State
  const [sharingModalConfig, setSharingModalConfig] = useState({ isOpen: false, data: null, target: null });
  const openSharingModal = (target, data) => {
    setSharingModalConfig({ isOpen: true, data: { ...data }, target });
  };
  const closeSharingModal = () => {
    setSharingModalConfig({ isOpen: false, data: null, target: null });
  };
  const handleSharingModalChange = (updatedData) => {
    setSharingModalConfig(prev => ({ ...prev, data: updatedData }));
    // Auto sync to target
    if (sharingModalConfig.target === 'newGoalData') {
      setNewGoalData(updatedData);
    } else if (sharingModalConfig.target === 'activeGoal') {
      setActiveGoal(updatedData);
    } else if (sharingModalConfig.target === 'newTaskData') {
      setNewTaskData(updatedData);
    } else if (sharingModalConfig.target === 'activeTask') {
      setActiveTask(updatedData);
      updateOrgTask(selectedOrg.slug, updatedData.id, {
        sharing_option: updatedData.sharing_option,
        assignees: updatedData.assignees,
        shared_viewers: updatedData.shared_viewers
      }).then(() => handleLoadTasks()).catch(console.error);
    }
  };
  // Leave States
  const [userLeaves, setUserLeaves] = useState([]);
  const [allLeaves, setAllLeaves] = useState([]);
  const [leaveBalances, setLeaveBalances] = useState([]);
  const [leavesViewTab, setLeavesViewTab] = useState('my-leaves');
  const [leaveForm, setLeaveForm] = useState({
    leave_type: 'Sick',
    start_date: '',
    end_date: '',
    reason: '',
    attachment: null
  });
  const [leaveLoading, setLeaveLoading] = useState(false);
  const [leaveError, setLeaveError] = useState('');
  const [leaveSuccess, setLeaveSuccess] = useState('');
  // Goals States
  const [goals, setGoals] = useState([]);
  const [activeGoal, setActiveGoal] = useState(null);
  const [goalsView, setGoalsView] = useState('list'); // 'list', 'create', 'detail', 'edit'
  const [newGoalData, setNewGoalData] = useState({
    title: '',
    description: '',
    owner: '',
    priority: 'medium',
    visibility_type: 'specific',
    visible_to: [],
    sharing_option: 'specific',
    assignees: [],
    shared_viewers: [],
    parent: '',
    depends_on: '',
    timeframe: 'quarterly',
    template_type: 'none',
    is_shared_externally: false
  });
  const [krForm, setKrForm] = useState({ title: '', target_value: 100.0, current_value: 0.0, unit: '%' });
  const [showAddKr, setShowAddKr] = useState(false);
  const [showAddGoalTask, setShowAddGoalTask] = useState(false);
  const [goalTaskForm, setGoalTaskForm] = useState({
    title: '', estimated_hours: '', estimated_minutes: '', assignees: []
  });
  // Tasks States
  const [tasks, setTasks] = useState([]);
  const [kanbanTickets, setKanbanTickets] = useState([]);
  const [activeTask, setActiveTask] = useState(null);
  const [activeTaskAssigneeSchedule, setActiveTaskAssigneeSchedule] = useState(null);
  const [liveActualMins, setLiveActualMins] = useState(0);
  const [tasksView, setTasksView] = useState('list'); // 'list', 'create', 'detail', 'edit'
  const [tasksLayout, setTasksLayout] = useState('list'); // 'list' or 'board'

const [taskSearchQuery, setTaskSearchQuery] = useState('');
const [taskStatusFilter, setTaskStatusFilter] = useState('all');
const [taskPriorityFilter, setTaskPriorityFilter] = useState('all');
const [newTaskData, setNewTaskData] = useState({
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
  
  if (assigneeId) {
    const member = orgMembers.find(m => (m.user?.id || m.user_id) === assigneeId);
    if (member && member.user && member.user.working_schedule) {
      setActiveTaskAssigneeSchedule(member.user.working_schedule);
    } else {
      setActiveTaskAssigneeSchedule(null);
    }
  } else {
    setActiveTaskAssigneeSchedule(null);
  }

  if (assigneeId && !isNaN(totalMins) && totalMins > 0 && !scheduledTime.manualOverride) {
    // Debounce the preview API call by 400ms to avoid calls on every keystroke
    const timer = setTimeout(async () => {
      setSchedulePreview(prev => ({ ...prev, isLoading: true }));
      try {
        if (selectedOrg && selectedOrg.id) {
          const estHours = totalMins / 60.0;
          const res = await getSchedulePreviewApi(selectedOrg.id, assigneeId, estHours);
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
    }, 400);
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
}, [newTaskData.assignees, newTaskData.estimated_minutes, selectedOrg, tasksView, scheduledTime.manualOverride]);


const [createAssignMode, setCreateAssignMode] = useState('manual');
const [createSmartSuggestions, setCreateSmartSuggestions] = useState([]);
const [createSmartSuggestLoading, setCreateSmartSuggestLoading] = useState(false);
const [createSmartSuggestError, setCreateSmartSuggestError] = useState(null);
const [editAssignMode, setEditAssignMode] = useState('manual');
const [editSmartSuggestions, setEditSmartSuggestions] = useState([]);
const [editSmartSuggestLoading, setEditSmartSuggestLoading] = useState(false);
const [editSmartSuggestError, setEditSmartSuggestError] = useState(null);
const [isFreeMembersModalOpen, setIsFreeMembersModalOpen] = useState(false);
const isMemberScheduleViewer = () => {
  const role = selectedOrg?.my_status?.role;
  const currentEmail = sessionStorage.getItem('email')?.toLowerCase();
  const creatorEmail = (selectedOrg?.created_by_email || selectedOrg?.creator_email || selectedOrg?.owner_email || '').toLowerCase();
  return role === 'owner' || role === 'admin' || (!!currentEmail && currentEmail === creatorEmail);
};
const formatScheduleTime = (value) => {
  if (!value) return 'N/A';
  return String(value).substring(0, 5);
};
const formatTaskDateTime = (value) => {
  if (!value) return 'N/A';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'N/A' : date.toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' });
};
const formatDurationMinutes = (minutes) => {
  const total = Math.max(0, Math.round(Number(minutes) || 0));
  const hrs = Math.floor(total / 60);
  const mins = total % 60;
  if (hrs && mins) return `${hrs}h ${mins}m`;
  if (hrs) return `${hrs}h`;
  return `${mins}m`;
};
const getMemberUserId = (member) => String(member?.user?.id || member?.user_id || member?.id || '');
const getTaskAssigneeId = (task) => String(
  task?.assignee ||
  task?.assignee_id ||
  task?.assignee_details?.[0]?.id ||
  task?.assignees?.[0] ||
  ''
);
const getLeaveUserId = (leave) => String(
  leave?.user ||
  leave?.user_id ||
  leave?.user_details?.id ||
  leave?.member_id ||
  ''
);
const getMemberSchedule = (member) => (
  member?.user?.working_schedule ||
  member?.working_schedule ||
  {
    work_start_time: '10:00:00',
    work_end_time: '19:00:00',
    lunch_break_start: '13:00:00',
    lunch_break_end: '14:00:00',
    tea_break_start: '17:00:00',
    tea_break_end: '17:30:00',
  }
);
const getTaskSpentMinutes = (task) => {
  if (task?.actual_time_spent_minutes != null) return Number(task.actual_time_spent_minutes) || 0;
  if (task?.actual_hours != null) return Math.round((Number(task.actual_hours) || 0) * 60);
  if (Array.isArray(task?.tickets)) {
    return task.tickets.reduce((sum, ticket) => sum + (Number(ticket.time_spent_minutes) || 0), 0);
  }
  return 0;
};
const getMemberStats = (member) => {
  const memberId = getMemberUserId(member);
  const memberEmail = member?.email?.toLowerCase();

  // Frontend-only aggregation: use already-loaded tasks/leaves so no backend
  // contract or scheduling logic changes are required for the member panels.
  const memberTasks = tasks.filter(task => getTaskAssigneeId(task) === memberId);
  const scheduledTasks = memberTasks
    .filter(task => task.planned_start || task.planned_end)
    .sort((a, b) => new Date(a.planned_start || 0) - new Date(b.planned_start || 0));
  const leaveRecords = allLeaves.filter(leave => {
    const leaveUserId = getLeaveUserId(leave);
    const leaveEmail = (leave?.user_details?.email || leave?.email || '').toLowerCase();
    return leaveUserId === memberId || (!!memberEmail && leaveEmail === memberEmail);
  });
  const totalSpentMinutes = memberTasks.reduce((sum, task) => sum + getTaskSpentMinutes(task), 0);
  const halfDays = leaveRecords.filter(leave =>
    String(leave.leave_type || '').toLowerCase().includes('half') ||
    Number(leave.number_of_days) === 0.5
  );

  return {
    schedule: getMemberSchedule(member),
    tasks: memberTasks,
    scheduledTasks,
    leaves: leaveRecords,
    halfDays,
    totalSpentMinutes,
  };
};
useEffect(() => {
  setEditAssignMode('manual');
  setEditSmartSuggestions([]);
  setEditSmartSuggestError(null);
}, [activeTask?.id]);
useEffect(() => {
  if (!activeTask || !activeTask.tickets || activeTask.tickets.length === 0) {
    setLiveActualMins(0);
    return;
  }
  const updateLiveTime = () => {
    let totalSeconds = 0;
    activeTask.tickets.forEach(ticket => {
      const savedSeconds = (ticket.time_spent_minutes || 0) * 60;
      let elapsed = savedSeconds;
      if (ticket.status === 'in_progress') {
        const startedAt = ticket.timer_started_at || ticket.updated_at;
        const timerStartMs = startedAt ? new Date(startedAt).getTime() : null;
        if (timerStartMs) {
          const liveRunningSeconds = Math.max(0, Math.floor((Date.now() - timerStartMs) / 1000));
          elapsed = savedSeconds + liveRunningSeconds;
        } else {
          const apiRunningSeconds = ticket.running_elapsed_seconds || 0;
          elapsed = savedSeconds + apiRunningSeconds;
        }
      } else {
        const apiTotalSeconds = Number.isFinite(ticket.total_elapsed_seconds)
          ? ticket.total_elapsed_seconds
          : savedSeconds;
        elapsed = apiTotalSeconds;
      }
      totalSeconds += elapsed;
    });
    setLiveActualMins(totalSeconds / 60);
  };
  updateLiveTime();
  const hasRunningTicket = activeTask.tickets.some(t => t.status === 'in_progress');
  if (hasRunningTicket) {
    const interval = setInterval(updateLiveTime, 1000);
    return () => clearInterval(interval);
  }
}, [activeTask?.tickets]);
// Task Comments State
const [comments, setComments] = useState([]);
const [newCommentText, setNewCommentText] = useState('');
const [feedbackModalConfig, setFeedbackModalConfig] = useState({ isOpen: false, taskId: null, taskTitle: '' });
const [submissionModalConfig, setSubmissionModalConfig] = useState({ isOpen: false, ticketId: null, taskId: null, taskTitle: '' });
const [submissionForm, setSubmissionForm] = useState({ comments: '', url_links: '', visibility: 'all', visible_to: [] });
const [submissionFile, setSubmissionFile] = useState(null);
const [extensionModalConfig, setExtensionModalConfig] = useState({ isOpen: false, taskId: null, taskTitle: '', currentDueDate: null });
const [isExtensionRequestsModalOpen, setIsExtensionRequestsModalOpen] = useState(false);
const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);
const [pendingExtensionCount, setPendingExtensionCount] = useState(0);
const [replyToCommentId, setReplyToCommentId] = useState(null);
const [editingCommentId, setEditingCommentId] = useState(null);
const [editingCommentText, setEditingCommentText] = useState('');
const [activeCommentDropdownId, setActiveCommentDropdownId] = useState(null);
const handleLoadComments = async (taskId) => {
  try {
    const data = await getTaskComments(taskId);
    setComments(data.comments || []);
  } catch (err) {
    console.error("Failed to load comments:", err);
  }
};
useEffect(() => {
  if (activeTask && activeTask.id) {
    handleLoadComments(activeTask.id);
  } else {
    setComments([]);
  }
}, [activeTask?.id]);
useEffect(() => {
  const handleGlobalClick = () => {
    setActiveCommentDropdownId(null);
  };
  window.addEventListener('click', handleGlobalClick);
  return () => window.removeEventListener('click', handleGlobalClick);
}, []);
const formatTimeAgo = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const seconds = Math.floor((now - date) / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
};
const handleCommentSubmit = async (e) => {
  if (e) e.preventDefault();
  if (!newCommentText.trim()) return;
  try {
    if (replyToCommentId) {
      await replyToComment(replyToCommentId, newCommentText);
    } else {
      await createTaskComment(activeTask.id, newCommentText, null);
    }
    setNewCommentText('');
    setReplyToCommentId(null);
    handleLoadComments(activeTask.id);
  } catch (err) {
    console.error("Failed to submit comment:", err);
  }
};
const handleCommentEdit = async (commentId) => {
  if (!editingCommentText.trim()) return;
  try {
    await updateTaskComment(commentId, editingCommentText);
    setEditingCommentId(null);
    setEditingCommentText('');
    handleLoadComments(activeTask.id);
  } catch (err) {
    console.error("Failed to edit comment:", err);
  }
};
const handleCommentDelete = (commentId) => {
  modal.showConfirmation("Are you sure you want to delete this comment?", async () => {
    try {
      await deleteTaskComment(commentId);
      handleLoadComments(activeTask.id);
    } catch (err) {
      console.error("Failed to delete comment:", err);
    }
  });
};
const renderCommentTree = (commentList) => {
  if (!commentList || commentList.length === 0) return null;
  return commentList.map((comment) => {
    const isAuthor = comment.user_id === profileData.id;
    const isEditing = editingCommentId === comment.id;
    const commentUserInitials = comment.user_name ? comment.user_name.split(' ').map(n => n[0]).join('').toUpperCase() : (comment.user_email ? comment.user_email[0].toUpperCase() : 'U');
    return (
      <div
        key={comment.id}
        style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem', position: 'relative' }}
        onContextMenu={(e) => {
          if (comment.is_deleted) return;
          e.preventDefault();
          e.stopPropagation();
          setActiveCommentDropdownId(comment.id);
        }}
      >
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
          {/* Avatar */}
          {comment.user_avatar ? (
            <img
              src={comment.user_avatar}
              alt={comment.user_name || comment.user_email}
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                objectFit: 'cover',
                flexShrink: 0,
                border: '1px solid #e2e8f0'
              }}
            />
          ) : (
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              backgroundColor: '#6366f1',
              color: 'white',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '0.75rem',
              fontWeight: '700',
              flexShrink: 0
            }}>
              {commentUserInitials}
            </div>
          )}
          {/* Message Body */}
          <div style={{ flex: 1, backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '0.75rem 1rem', position: 'relative' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: '700', color: '#0f172a' }}>{comment.user_name || comment.user_email}</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>
                  {formatTimeAgo(comment.created_at)}
                  {comment.is_edited && <span style={{ marginLeft: '0.35rem', fontStyle: 'italic', color: '#6366f1', fontWeight: 500 }}>(edited)</span>}
                </span>
                {!comment.is_deleted && (
                  <div style={{ position: 'relative' }}>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setActiveCommentDropdownId(activeCommentDropdownId === comment.id ? null : comment.id);
                      }}
                      style={{ border: 'none', background: 'none', cursor: 'pointer', padding: '2px', color: '#94a3b8', display: 'flex', alignItems: 'center' }}
                    >
                      <MoreVertical size={14} />
                    </button>
                    {activeCommentDropdownId === comment.id && (
                      <div style={{
                        position: 'absolute',
                        top: '100%',
                        right: 0,
                        backgroundColor: 'white',
                        border: '1px solid #e2e8f0',
                        borderRadius: '8px',
                        boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06)',
                        zIndex: 50,
                        minWidth: '120px',
                        display: 'flex',
                        flexDirection: 'column',
                        padding: '0.25rem'
                      }}>
                        <button
                          onClick={() => {
                            setReplyToCommentId(comment.id);
                            setActiveCommentDropdownId(null);
                          }}
                          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', border: 'none', background: 'none', padding: '0.5rem', fontSize: '0.75rem', width: '100%', textAlign: 'left', cursor: 'pointer', color: '#475569', borderRadius: '4px' }}
                          onMouseEnter={(e) => e.target.style.backgroundColor = '#f1f5f9'}
                          onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
                        >
                          <MessageSquare size={12} /> Reply
                        </button>
                        {isAuthor && (
                          <>
                            <button
                              onClick={() => {
                                setEditingCommentId(comment.id);
                                setEditingCommentText(comment.comment);
                                setActiveCommentDropdownId(null);
                              }}
                              style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', border: 'none', background: 'none', padding: '0.5rem', fontSize: '0.75rem', width: '100%', textAlign: 'left', cursor: 'pointer', color: '#475569', borderRadius: '4px' }}
                              onMouseEnter={(e) => e.target.style.backgroundColor = '#f1f5f9'}
                              onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
                            >
                              <Edit3 size={12} /> Edit
                            </button>
                            <button
                              onClick={() => {
                                handleCommentDelete(comment.id);
                                setActiveCommentDropdownId(null);
                              }}
                              style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', border: 'none', background: 'none', padding: '0.5rem', fontSize: '0.75rem', width: '100%', textAlign: 'left', cursor: 'pointer', color: '#ef4444', borderRadius: '4px' }}
                              onMouseEnter={(e) => e.target.style.backgroundColor = '#fee2e2'}
                              onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
                            >
                              <Trash2 size={12} /> Delete
                            </button>
                          </>
                        )}
                        <button
                          onClick={() => {
                            setNewCommentText(`[Reposting]: "${comment.comment}"`);
                            setActiveCommentDropdownId(null);
                          }}
                          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', border: 'none', background: 'none', padding: '0.5rem', fontSize: '0.75rem', width: '100%', textAlign: 'left', cursor: 'pointer', color: '#475569', borderRadius: '4px' }}
                          onMouseEnter={(e) => e.target.style.backgroundColor = '#f1f5f9'}
                          onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
                        >
                          <Repeat size={12} /> Repost
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
            {isEditing ? (
              <div style={{ marginTop: '0.5rem' }}>
                <textarea
                  value={editingCommentText}
                  onChange={(e) => setEditingCommentText(e.target.value)}
                  style={{
                    width: '100%',
                    minHeight: '60px',
                    padding: '0.5rem',
                    borderRadius: '8px',
                    border: '1px solid #cbd5e1',
                    fontSize: '0.85rem',
                    outline: 'none',
                    fontFamily: 'inherit'
                  }}
                />
                <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
                  <button
                    onClick={() => handleCommentEdit(comment.id)}
                    style={{ backgroundColor: '#6366f1', color: 'white', border: 'none', borderRadius: '6px', padding: '0.25rem 0.75rem', fontSize: '0.75rem', fontWeight: '600', cursor: 'pointer' }}
                  >
                    Save
                  </button>
                  <button
                    onClick={() => { setEditingCommentId(null); setEditingCommentText(''); }}
                    style={{ backgroundColor: '#e2e8f0', color: '#475569', border: 'none', borderRadius: '6px', padding: '0.25rem 0.75rem', fontSize: '0.75rem', fontWeight: '600', cursor: 'pointer' }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <p style={{
                fontSize: '0.85rem',
                color: comment.is_deleted ? '#94a3b8' : '#334155',
                margin: '0.25rem 0',
                lineHeight: '1.4',
                whiteSpace: 'pre-wrap',
                fontStyle: comment.is_deleted ? 'italic' : 'normal'
              }}>
                {comment.comment}
              </p>
            )}
            {/* Attachments rendering */}
            {comment.attachments && comment.attachments.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.75rem' }}>
                {comment.attachments.map(att => {
                  const isImg = /\.(jpg|jpeg|png|gif|webp)$/i.test(att.file);
                  return (
                    <a
                      key={att.id}
                      href={att.file}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ textDecoration: 'none', color: 'inherit' }}
                    >
                      {isImg ? (
                        <div style={{ position: 'relative', width: '80px', height: '80px', borderRadius: '8px', overflow: 'hidden', border: '1px solid #e2e8f0', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
                          <img src={att.file} alt={att.file_name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                        </div>
                      ) : (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '0.4rem 0.6rem', fontSize: '0.75rem' }}>
                          <Paperclip size={14} style={{ color: '#64748b' }} />
                          <span style={{ maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontWeight: 500, color: '#475569' }}>{att.file_name}</span>
                        </div>
                      )}
                    </a>
                  );
                })}
              </div>
            )}
          </div>
        </div>
        {/* Child replies */}
        {comment.replies && comment.replies.length > 0 && (
          <div style={{ marginLeft: '1.5rem', borderLeft: '2px solid #f1f5f9', paddingLeft: '1rem', marginTop: '0.25rem' }}>
            {renderCommentTree(comment.replies)}
          </div>
        )}
      </div>
    );
  });
};
// Live clock — updates every minute
const [liveTime, setLiveTime] = useState(new Date());
useEffect(() => {
  const tick = setInterval(() => setLiveTime(new Date()), 60000);
  return () => clearInterval(tick);
}, []);
// Resizable sidebar states & drag handlers
const [taskSidebarWidth, setTaskSidebarWidth] = useState(320);
const [notesSidebarWidth, setNotesSidebarWidth] = useState(260);
const [permissionsSidebarWidth, setPermissionsSidebarWidth] = useState(320);
const handleTaskSidebarResize = (mouseDownEvent) => {
  mouseDownEvent.preventDefault();
  const startWidth = taskSidebarWidth;
  const startX = mouseDownEvent.clientX;
  const doDrag = (moveEvent) => {
    const newWidth = Math.max(240, Math.min(600, startWidth - (moveEvent.clientX - startX)));
    setTaskSidebarWidth(newWidth);
  };
  const stopDrag = () => {
    document.removeEventListener('mousemove', doDrag);
    document.removeEventListener('mouseup', stopDrag);
  };
  document.addEventListener('mousemove', doDrag);
  document.addEventListener('mouseup', stopDrag);
};
const handleNotesSidebarResize = (mouseDownEvent) => {
  mouseDownEvent.preventDefault();
  const startWidth = notesSidebarWidth;
  const startX = mouseDownEvent.clientX;
  const doDrag = (moveEvent) => {
    const newWidth = Math.max(180, Math.min(450, startWidth + (moveEvent.clientX - startX)));
    setNotesSidebarWidth(newWidth);
  };
  const stopDrag = () => {
    document.removeEventListener('mousemove', doDrag);
    document.removeEventListener('mouseup', stopDrag);
  };
  document.addEventListener('mousemove', doDrag);
  document.addEventListener('mouseup', stopDrag);
};
const handlePermissionsSidebarResize = (mouseDownEvent) => {
  mouseDownEvent.preventDefault();
  const startWidth = permissionsSidebarWidth;
  const startX = mouseDownEvent.clientX;
  const doDrag = (moveEvent) => {
    const newWidth = Math.max(240, Math.min(500, startWidth + (moveEvent.clientX - startX)));
    setPermissionsSidebarWidth(newWidth);
  };
  const stopDrag = () => {
    document.removeEventListener('mousemove', doDrag);
    document.removeEventListener('mouseup', stopDrag);
  };
  document.addEventListener('mousemove', doDrag);
  document.addEventListener('mouseup', stopDrag);
};
const getLogoUrl = (logoPath) => {
  if (!logoPath) return null;
  if (logoPath.startsWith('http')) return logoPath;
  return `http://localhost:8000${logoPath}`;
};
const [formData, setFormData] = useState({
  email: '',
  password: '',
  new_password: '',
  confirm_password: ''
});
const [editOrgData, setEditOrgData] = useState({ name: '', description: '', logo: null });
// Profile & Password States
const [profileData, setProfileData] = useState({
  id: '',
  email: '',
  first_name: '',
  last_name: '',
  phone: '',
  education: '',
  job_title: '',
  department: '',
  date_of_birth: '',
  bio: '',
  profile_picture: null,
  profile_picture_preview: null,
  // Working schedule defaults (mirrors backend model defaults)
  work_start_time: '10:00:00',
  work_end_time: '19:00:00',
  lunch_break_start: '13:00:00',
  lunch_break_end: '14:00:00',
  tea_break_start: '17:00:00',
  tea_break_end: '17:30:00',
});
const [newEmail, setNewEmail] = useState('');
const [emailChangePassword, setEmailChangePassword] = useState('');
const [emailChangeStep, setEmailChangeStep] = useState('request'); // 'request' or 'verify'
const [emailOtp, setEmailOtp] = useState(['', '', '', '', '', '']);
const [changePasswordData, setChangePasswordData] = useState({ new_password: '', confirm_password: '' });
const [selectedMemberId, setSelectedMemberId] = useState(null);
const [showWorkspaceDropdown, setShowWorkspaceDropdown] = useState(false);
const [searchQuery, setSearchQuery] = useState('');
const [workspaceHistory, setWorkspaceHistory] = useState([]);
const [historySubTab, setHistorySubTab] = useState('logs');
const [selectedHistoryLog, setSelectedHistoryLog] = useState(null);
const [permissionsSubTab, setPermissionsSubTab] = useState('members');
const [selectedPermissionMember, setSelectedPermissionMember] = useState(null);
const [activeJoinRequest, setActiveJoinRequest] = useState(null);
// Notebook and Calendar States
const [notes, setNotes] = useState([]);
const [showNotebook, setShowNotebook] = useState(false);
const [activeNote, setActiveNote] = useState(null);
const [noteTitle, setNoteTitle] = useState('');
const [noteContent, setNoteContent] = useState('');
const [savingNote, setSavingNote] = useState(false);
const [showCalendarPopover, setShowCalendarPopover] = useState(false);
useEffect(() => {
  if (selectedOrg) {
    setEditOrgData({
      name: selectedOrg.name || '',
      description: selectedOrg.description || '',
      logo: null
    });
  }
}, [selectedOrg]);
useEffect(() => {
  if (activeTab === 'tasks' && selectedOrg) {
    handleLoadTasks();
  }
}, [activeTab, selectedOrg]);
const handleLoadTasks = async () => {
  if (!selectedOrg) return;
  try {
    const data = await getOrgTasks(selectedOrg.slug);
    const taskList = Array.isArray(data) ? data : (data.results || data.tasks || []);
    setTasks(taskList);
    const kanbanData = await getTasksKanban(selectedOrg.id);
    setKanbanTickets(Array.isArray(kanbanData) ? kanbanData : []);
    if (activeTask) {
      try {
        const freshTaskDetail = await getOrgTaskDetail(selectedOrg.slug, activeTask.id);
        setActiveTask(freshTaskDetail);
      } catch (err) {
        console.error('Failed to load fresh task details:', err);
        const freshTask = taskList.find(t => t.id === activeTask.id);
        if (freshTask) {
          setActiveTask(prev => {
            if (!prev) return freshTask;
            return { ...prev, ...freshTask };
          });
        }
      }
    }
  } catch (err) {
    console.error('Failed to load tasks:', err);
  }
};

const handleRunScheduler = async () => {
  if (!selectedOrg) return;
  setLoading(true);
  try {
    const res = await runScheduler(selectedOrg.slug);
    alert(res.message);
    handleLoadTasks();
  } catch (err) {
    alert(err.response?.data?.error || "Failed to run scheduler.");
  } finally {
    setLoading(false);
  }
};

const handleCSVUpload = async (e) => {
  if (!selectedOrg || !e.target.files[0]) return;
  setLoading(true);
  try {
    const res = await importTasksCSV(selectedOrg.slug, e.target.files[0]);
    alert(res.message);
    handleLoadTasks();
  } catch (err) {
    alert(err.response?.data?.error || "Failed to import CSV.");
  } finally {
    setLoading(false);
    e.target.value = null;
  }
};
const handleUpdateTicketStatus = async (ticketId, nextStatus) => {
  try {
    // Optimistic UI update
    setKanbanTickets(prev => prev.map(t => t.id === ticketId ? { ...t, status: nextStatus } : t));
    // Send PATCH call to backend
    const updatedTicket = await updateTaskTicketStatus(ticketId, nextStatus);
    setKanbanTickets(prev => prev.map(t => t.id === ticketId ? { ...t, ...updatedTicket } : t));
    // If marked as done, open the feedback modal (if we have access to the task details)
    // Since ticketId is what we have, we should find the ticket in kanbanTickets to get the task
    if (nextStatus === 'done') {
      const ticket = kanbanTickets.find(t => t.id === ticketId);
      if (ticket && ticket.task_details) {
        setFeedbackModalConfig({ isOpen: true, taskId: ticket.task_details.id, taskTitle: ticket.task_details.title });
      }
    }
    // Reload everything to keep state fully in sync
    await handleLoadTasks();
    return updatedTicket;
  } catch (err) {
    console.error('Failed to update ticket status:', err);
    const errMsg = err.response?.data?.error || err.response?.data?.detail || 'You do not have permission to update this ticket.';
    if (errMsg.includes('already has another task In Progress') || errMsg.includes('already has another task') || errMsg.includes('already has another task in progress')) {
      setWorkloadLimitWarning(errMsg);
    } else {
      setError(errMsg);
    }
    // Revert if error
    await handleLoadTasks();
    throw err;
  }
};
const handleDashboardNavigation = (tab, filters) => {
  setActiveTab(tab);
  if (tab === 'tasks') {
    setTasksView('list');
    handleLoadTasks();
    if (filters?.filter === 'overdue') {
      setTaskStatusFilter('overdue');
    } else if (filters?.filter === 'completed') {
      setTaskStatusFilter('done');
    } else {
      setTaskStatusFilter('all');
    }
  } else if (tab === 'goals') {
    setGoalsView('list');
    handleLoadGoals();
  }
};
const handleTaskClick = async (task) => {
  setLoading(true);
  try {
    const detailedTask = await getOrgTaskDetail(selectedOrg.slug, task.id);
    setActiveTask(detailedTask);
    // Use the assignee's schedule for bidirectional sync if available, else fall back to logged-in user's
    const assigneeSchedule = detailedTask?.assignee_schedule || detailedTask?.assignee_working_schedule || null;
    setActiveTaskAssigneeSchedule(assigneeSchedule);
    setTasksView('detail');
  } catch (err) {
    console.error('Failed to load task details:', err);
    setActiveTask(task);
    setActiveTaskAssigneeSchedule(null);
    setTasksView('detail');
  } finally {
    setLoading(false);
  }
};
const enablePushNotifications = async () => {
  try {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
      console.warn('Push messaging is not supported by this browser.');
      return;
    }
    const permission = await Notification.requestPermission();
    if (permission !== 'granted') {
      console.warn('Push notification permission denied.');
      return;
    }
    const reg = await navigator.serviceWorker.register('/sw.js');
    const publicVapidKey = "BGxvCf-KPDJcxD0u0wcT7QvgCJZDKQvlLzwoN-n5x2Wf0FR8opipIsdjylf5g8rp9szZGsCWpO7CnS6DYbF1wk8";
    function urlBase64ToUint8Array(base64String) {
      const padding = '='.repeat((4 - base64String.length % 4) % 4);
      const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
      const rawData = window.atob(base64);
      const outputArray = new Uint8Array(rawData.length);
      for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
      }
      return outputArray;
    }
    const subscription = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(publicVapidKey)
    });
    const subJson = subscription.toJSON();
    await saveWebPushSubscription({
      endpoint: subJson.endpoint,
      p256dh: subJson.keys.p256dh,
      auth: subJson.keys.auth
    });
    console.log('Web Push Subscription saved successfully.');
  } catch (err) {
    console.error('Failed to subscribe to web push:', err);
  }
};
const fetchNotifications = async () => {
  // Disabled notifications fetching
  setNotifications([]);
};
const handleMarkRead = async (id) => {
  try {
    sessionStorage.setItem(`read_at_${id}`, Date.now().toString());
    await markNotificationRead(id);
    fetchNotifications();
  } catch (err) {
    console.error('Failed to mark notification read:', err);
  }
};
const handleMarkAllRead = async () => {
  try {
    notifications.forEach(n => {
      if (!n.is_read) {
        sessionStorage.setItem(`read_at_${n.id}`, Date.now().toString());
      }
    });
    await markAllNotificationsRead(selectedOrg?.slug);
    fetchNotifications();
  } catch (err) {
    console.error('Failed to mark all notifications read:', err);
  }
};
const handleAcceptInvite = async (e, invitationId, notifId) => {
  e.stopPropagation();
  setLoading(true);
  setError('');
  setMessage('');
  try {
    const res = await acceptInvitation(invitationId);
    setMessage(res.message || 'Invitation accepted successfully!');
    sessionStorage.setItem(`read_at_${notifId}`, Date.now().toString());
    await markNotificationRead(notifId);
    await fetchWorkspaces(null, true);
    await fetchNotifications();
  } catch (err) {
    setError(err.response?.data?.error || 'Failed to accept invitation');
  } finally {
    setLoading(false);
  }
};
const handleDeclineInvite = async (e, invitationId, notifId) => {
  e.stopPropagation();
  setLoading(true);
  setError('');
  setMessage('');
  try {
    const res = await declineInvitation(invitationId);
    setMessage(res.message || 'Invitation declined successfully!');
    sessionStorage.setItem(`read_at_${notifId}`, Date.now().toString());
    await markNotificationRead(notifId);
    await fetchNotifications();
    await fetchWorkspaces(null, false);
  } catch (err) {
    setError(err.response?.data?.error || 'Failed to decline invitation');
  } finally {
    setLoading(false);
  }
};
const handleNotificationClick = async (notif) => {
  if (!notif.is_read) {
    await handleMarkRead(notif.id);
  }
  setShowNotifications(false);
  const orgId = notif.data?.organization_id;
  if (!orgId) return;
  if (notif.notification_type === 'join_request') {
    const org = organizations.find(o => o.id === orgId);
    if (org) {
      await handleEnterWorkspace(org);
      setActiveTab('permissions');
    } else {
      try {
        const allOrgs = await getOrganizations();
        setOrganizations(allOrgs);
        const freshOrg = allOrgs.find(o => o.id === orgId);
        if (freshOrg) {
          await handleEnterWorkspace(freshOrg);
          setActiveTab('permissions');
        }
      } catch (err) {
        console.error('Failed to locate workspace for notification:', err);
      }
    }
  } else if (notif.notification_type === 'join_request_approved') {
    await fetchWorkspaces(null, false);
    const org = organizations.find(o => o.id === orgId);
    if (org) {
      await handleEnterWorkspace(org);
    } else {
      setView('onboarding');
    }
  } else if (notif.notification_type === 'join_request_denied') {
    await fetchWorkspaces(null, false);
    setView('onboarding');
  } else if (['invitation'].includes(notif.notification_type)) {
    // Just stay on current or go to notifications history
    setActiveTab('history');
    setHistorySubTab('notifications');
  } else {
    // General routing based on keywords
    const typeStr = notif.notification_type || '';
    let targetTab = 'overview';
    if (typeStr.includes('task') || typeStr.includes('comment')) targetTab = 'tasks';
    else if (typeStr.includes('goal')) targetTab = 'goals';
    else if (typeStr.includes('note')) targetTab = 'notes';
    const navigateToTab = async (orgToEnter) => {
      await handleEnterWorkspace(orgToEnter);
      setActiveTab(targetTab);
      const link = notif.data?.link || '';
      if (targetTab === 'tasks') {
        if (link.startsWith('/tasks/')) {
          const taskId = link.split('/').pop();
          try {
            const taskDetail = await getOrgTaskDetail(orgToEnter.slug, taskId);
            setActiveTask(taskDetail);
            setTasksView('detail');
          } catch (err) {
            console.error('Failed to load task from notification', err);
            setTasksView('list');
          }
        } else {
          setTasksView('list');
        }
      }
      if (targetTab === 'goals') {
        if (link.startsWith('/goals/')) {
          const goalId = link.split('/').pop();
          try {
            const goalDetail = await getOrgGoalDetail(orgToEnter.slug, goalId);
            setActiveGoal(goalDetail);
            setGoalsView('detail');
          } catch (err) {
            console.error('Failed to load goal from notification', err);
            setGoalsView('list');
          }
        } else {
          setGoalsView('list');
        }
      }
    };
    const org = organizations.find(o => o.id === orgId);
    if (org) {
      await navigateToTab(org);
    } else {
      try {
        const allOrgs = await getOrganizations();
        setOrganizations(allOrgs);
        const freshOrg = allOrgs.find(o => o.id === orgId);
        if (freshOrg) {
          await navigateToTab(freshOrg);
        }
      } catch (err) {
        console.error('Failed to locate workspace for notification:', err);
      }
    }
  }
};
useEffect(() => {
  if (isLoggedIn) {
    const token = sessionStorage.getItem('access_token');
    if (token) {
      setAuthTokens(token);
    }
    fetchWorkspaces();
  }
}, [isLoggedIn]);
useEffect(() => {
  if (isLoggedIn) {
    fetchNotifications();
    // Poll every 15 seconds for real-time notifications
    const interval = setInterval(fetchNotifications, 15000);
    return () => clearInterval(interval);
  }
}, [isLoggedIn, selectedOrg]);
// Fetch pending extension count for admins/owners
useEffect(() => {
  if (selectedOrg && (selectedOrg.my_status?.role === 'owner' || selectedOrg.my_status?.role === 'admin')) {
    const fetchExtensions = async () => {
      try {
        const data = await getExtensionRequests(selectedOrg.id);
        const reqs = data.results || data;
        setPendingExtensionCount(reqs.filter(r => r.status === 'pending').length);
      } catch (e) {
        console.error("Failed to load extension count", e);
      }
    };
    fetchExtensions();
  }
}, [selectedOrg, isExtensionRequestsModalOpen]);
// Auto-mark all unread notifications as read after 2s when popover is opened
useEffect(() => {
  if (!showNotifications) return;
  const unread = notifications.filter(n => !n.is_read);
  if (unread.length === 0) return;
  const timer = setTimeout(async () => {
    try {
      unread.forEach(n => {
        sessionStorage.setItem(`read_at_${n.id}`, Date.now().toString());
      });
      await markAllNotificationsRead(selectedOrg?.slug);
      await fetchNotifications();
    } catch (err) {
      console.error('Auto-mark-read failed:', err);
    }
  }, 2000);
  return () => clearTimeout(timer);
}, [showNotifications, notifications]);
// Clear success and error messages when switching views/tabs/organizations
useEffect(() => {
  setMessage('');
  setError('');
}, [activeTab, view, selectedOrg]);
useEffect(() => {
  if ((activeTab === 'settings' || activeTab === 'profile') && isLoggedIn) {
    handleLoadProfile();
  }
}, [activeTab, isLoggedIn]);
useEffect(() => {
  if (activeTab === 'leaves' && selectedOrg && isLoggedIn) {
    handleLoadLeaves();
  }
}, [activeTab, selectedOrg, isLoggedIn]);
useEffect(() => {
  if (activeTab === 'members' && selectedOrg && isLoggedIn && isMemberScheduleViewer()) {
    handleLoadTasks();
    handleLoadLeaves();
  }
}, [activeTab, selectedOrg, isLoggedIn]);
// Auto-clear success message after 5 seconds
useEffect(() => {
  if (message) {
    const timer = setTimeout(() => {
      setMessage('');
    }, 5000);
    return () => clearTimeout(timer);
  }
}, [message]);
// Auto-clear error message after 8 seconds
useEffect(() => {
  if (error) {
    const timer = setTimeout(() => {
      setError('');
    }, 8000);
    return () => clearTimeout(timer);
  }
}, [error]);
useEffect(() => {
  const handleClosePopovers = () => {
    setShowNotifications(false);
    setShowWorkspaceDropdown(false);
    setShowCalendarPopover(false);
  };
  window.addEventListener('click', handleClosePopovers);
  return () => window.removeEventListener('click', handleClosePopovers);
}, []);
useEffect(() => {
  const handleSAMLCallback = async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const access = urlParams.get('access');
    const refresh = urlParams.get('refresh');
    const errorParam = urlParams.get('error');
    if (errorParam) {
      setError(decodeURIComponent(errorParam));
      const cleanUrl = window.location.origin + window.location.pathname;
      window.history.replaceState({}, document.title, cleanUrl);
      return;
    }
    if (access && refresh) {
      setView('connecting_sso');
      setError('');
      try {
        console.log('SAML authentication successful, initializing session...');
        setAuthTokens(access, refresh);
        const profileData = await getUserProfile();
        sessionStorage.setItem('email', profileData.email);
        setIsLoggedIn(true);
        await fetchWorkspaces(access);
        const cleanUrl = window.location.origin + window.location.pathname + window.location.hash;
        window.history.replaceState({}, document.title, cleanUrl);
      } catch (err) {
        console.error('SAML login session creation failed:', err);
        setError(err.response?.data?.error || err.response?.data?.detail || 'SSO authentication failed.');
        setView('login');
        setAuthTokens(null);
        const cleanUrl = window.location.origin + window.location.pathname + window.location.hash;
        window.history.replaceState({}, document.title, cleanUrl);
      }
    }
  };
  handleSAMLCallback();
}, []);

useEffect(() => {
  const handleInvitationToken = async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token') || urlParams.get('invitation_token');
    if (token) {
      setLoading(true);
      try {
        if (!sessionStorage.getItem('access')) {
          sessionStorage.setItem('pending_invite_token', token);
          setMessage('Please login with your temporary password to accept the invitation.');
          setView('login');
          const cleanUrl = window.location.origin + window.location.pathname + window.location.hash;
          window.history.replaceState({}, document.title, cleanUrl);
          setLoading(false);
          return;
        }

        const res = await acceptInvitation(null, token);
        setMessage('Invitation accepted successfully! You can now access the workspace.');
        const cleanUrl = window.location.origin + window.location.pathname + window.location.hash;
        window.history.replaceState({}, document.title, cleanUrl);
        
        if (sessionStorage.getItem('access')) {
          await fetchWorkspaces(sessionStorage.getItem('access'), false);
        } else {
          setView('login');
          setLoading(false);
          return;
        }
        setView('onboarding');
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to accept invitation. It may be invalid or expired.');
        const cleanUrl = window.location.origin + window.location.pathname + window.location.hash;
        window.history.replaceState({}, document.title, cleanUrl);
      } finally {
        setLoading(false);
      }
    }
  };
  handleInvitationToken();
}, []);
const fetchWorkspaces = async (manualToken = null, shouldRedirect = true) => {
  setLoading(true);
  setError(null);
  try {
    // If a token is provided manually (after login), ensure it's set before fetching
    if (manualToken) {
      setAuthTokens(manualToken);
    }
    const allOrgs = await getOrganizations();
    console.log('Workspaces fetched successfully:', allOrgs.length);
    setOrganizations(allOrgs);
    if (shouldRedirect) {
      const savedOrgId = sessionStorage.getItem('selectedOrgId');
      const memberOrgs = allOrgs.filter(o => o.my_status?.type === 'member');
      if (savedOrgId && memberOrgs.some(o => o.id === savedOrgId)) {
        const savedOrg = memberOrgs.find(o => o.id === savedOrgId);
        handleEnterWorkspace(savedOrg, true);
      } else {
        setView('onboarding');
      }
    }
  } catch (err) {
    console.error('Fetch workspaces error details:', err.response || err);
    const status = err.response?.status;
    if (status === 401) {
      setError('Session expired or unauthorized. Please login again.');
      setView('login');
    } else {
      setError(`Failed to load workspaces: ${err.response?.data?.error || err.message}`);
      // Stay on onboarding if we have data, otherwise login
      if (organizations.length === 0) setView('login');
    }
  } finally {
    setLoading(false);
  }
};
const handleOtpChange = (index, value) => {
  // If value is multiple characters, it's likely a paste or autofill
  if (value.length > 1) {
    const pastedOtp = value.split('').filter(char => !isNaN(char)).slice(0, 6);
    const newOtp = [...otp];
    pastedOtp.forEach((char, i) => {
      if (index + i < 6) newOtp[index + i] = char;
    });
    setOtp(newOtp);
    // Focus the last filled input or the next one
    const lastIndex = Math.min(index + pastedOtp.length - 1, 5);
    if (lastIndex < 5) otpRefs.current[lastIndex + 1].focus();
    else otpRefs.current[5].focus();
    return;
  }
  if (isNaN(value)) return;
  const newOtp = [...otp];
  newOtp[index] = value;
  setOtp(newOtp);
  if (value && index < 5) otpRefs.current[index + 1].focus();
};
const handlePaste = (e) => {
  const pastedData = e.clipboardData.getData('text').trim();
  if (pastedData.length === 6 && !isNaN(pastedData)) {
    const newOtp = pastedData.split('');
    setOtp(newOtp);
    otpRefs.current[5].focus();
  }
};
const handleKeyDown = (index, e) => {
  if (e.key === 'Backspace' && !otp[index] && index > 0) {
    otpRefs.current[index - 1].focus();
  }
};
const handleCreateOrganization = async (e) => {
  if (e) e.preventDefault();
  setLoading(true);
  setError('');
  setMessage('');
  try {
    const { name, description } = newOrgData;
    const createdOrg = await createOrganization({ name, description });
    setMessage('Workspace created successfully!');
    setNewOrgData({ name: '', description: '', useCase: '', initialInvites: '' });
    setCreateOrgStep(1);
    await fetchWorkspaces(null, false);
    const formattedOrg = {
      ...createdOrg,
      my_status: { type: 'member', role: 'owner' }
    };
    await handleEnterWorkspace(formattedOrg);
  } catch (err) {
    setError(err.response?.data?.error || err.response?.data?.detail || 'Failed to create workspace');
  } finally {
    setLoading(false);
  }
};
const handleJoinRequest = async (orgId) => {
  const role = selectedRoles[orgId];
  if (!role) {
    setError('Please select a role first');
    return;
  }
  setLoading(true);
  try {
    await sendJoinRequest(orgId, role, joinMessage);
    setMessage('Join request sent!');
    setShowJoinModal(false);
    setJoinMessage('');
    fetchWorkspaces();
  } catch (err) {
    setError(err.response?.data?.error || 'Failed to send request');
  } finally {
    setLoading(false);
  }
};
const handleAcceptInvitation = async (org, invitationId) => {
  setLoading(true);
  setError(null);
  setMessage(null);
  try {
    await acceptInvitation(invitationId);
    setMessage(`Successfully accepted invitation to ${org.name}!`);
    const updatedOrgs = await getOrganizations();
    setOrganizations(updatedOrgs);
    const freshOrg = updatedOrgs.find(o => o.id === org.id);
    if (freshOrg) {
      await handleEnterWorkspace(freshOrg);
    }
  } catch (err) {
    setError(err.response?.data?.error || err.response?.data?.detail || 'Failed to accept invitation');
  } finally {
    setLoading(false);
  }
};
const handleUpdateOrgSettings = async (e) => {
  e.preventDefault();
  setLoading(true);
  setError('');
  setMessage('');
  try {
    const fd = new FormData();
    fd.append('name', editOrgData.name);
    fd.append('description', editOrgData.description);
    if (editOrgData.logo instanceof File) {
      fd.append('logo', editOrgData.logo);
    }
    const updated = await updateOrganization(selectedOrg.id, fd);
    setMessage('Workspace settings updated successfully!');
    const mergedOrg = {
      ...updated,
      my_status: selectedOrg.my_status
    };
    setSelectedOrg(mergedOrg);
    fetchWorkspaces(null, false);
  } catch (err) {
    setError(err.response?.data?.error || err.response?.data?.detail || 'Failed to update workspace settings');
  } finally {
    setLoading(false);
  }
};
const handleDeactivateOrg = async () => {
  setLoading(true);
  setConfirmModalError('');
  setError('');
  setMessage('');
  try {
    await deactivateOrganization(selectedOrg.id);
    setMessage('Workspace deactivated successfully.');
    setConfirmInput('');
    setView('onboarding');
    setSelectedOrg(null);
    fetchWorkspaces(null, false);
  } catch (err) {
    setConfirmModalError(err.response?.data?.error || err.response?.data?.detail || 'Failed to deactivate workspace');
  } finally {
    setLoading(false);
  }
};
const handlePermanentDeleteOrg = async () => {
  setLoading(true);
  setConfirmModalError('');
  setError('');
  setMessage('');
  try {
    await deleteOrganization(selectedOrg.id);
    setMessage('Workspace permanently deleted.');
    setConfirmInput('');
    setView('onboarding');
    setSelectedOrg(null);
    fetchWorkspaces(null, false);
  } catch (err) {
    setConfirmModalError(err.response?.data?.error || err.response?.data?.detail || 'Failed to delete workspace');
  } finally {
    setLoading(false);
  }
};
const handleReactivateOrg = async (orgId) => {
  setLoading(true);
  setError('');
  setMessage('');
  try {
    await reactivateOrganization(orgId);
    setMessage('Workspace reactivated successfully!');
    fetchWorkspaces(null, false);
  } catch (err) {
    setError(err.response?.data?.error || err.response?.data?.detail || 'Failed to reactivate workspace');
  } finally {
    setLoading(false);
  }
};
const handleLoadProfile = async () => {
  try {
    setLoading(true);
    const data = await getUserProfile();
    setProfileData({
      id: data.id || '',
      email: data.email || '',
      first_name: data.first_name || '',
      last_name: data.last_name || '',
      phone: data.phone || '',
      education: data.education || '',
      job_title: data.job_title || '',
      department: data.department || '',
      date_of_birth: data.date_of_birth || '',
      bio: data.bio || '',
      work_start_time: data.working_schedule?.work_start_time || data.work_start_time || '10:00:00',
      work_end_time: data.working_schedule?.work_end_time || data.work_end_time || '19:00:00',
      lunch_break_start: data.working_schedule?.lunch_break_start || data.lunch_break_start || '13:00:00',
      lunch_break_end: data.working_schedule?.lunch_break_end || data.lunch_break_end || '14:00:00',
      tea_break_start: data.working_schedule?.tea_break_start || data.tea_break_start || '17:00:00',
      tea_break_end: data.working_schedule?.tea_break_end || data.tea_break_end || '17:30:00',
      profile_picture: null,
      profile_picture_preview: data.profile_picture ? (data.profile_picture.startsWith('http') ? data.profile_picture : `http://localhost:8000${data.profile_picture}`) : null
    });
    setNewEmail(data.email || '');
  } catch (err) {
    setError(err.response?.data?.error || 'Failed to load user profile.');
  } finally {
    setLoading(false);
  }
};
const handleUpdateProfile = async (e) => {
  e.preventDefault();
  setLoading(true);
  setError('');
  setMessage('');
  try {
    const fd = new FormData();
    fd.append('first_name', profileData.first_name);
    fd.append('last_name', profileData.last_name);
    fd.append('phone', profileData.phone);
    fd.append('education', profileData.education);
    fd.append('job_title', profileData.job_title);
    fd.append('department', profileData.department);
    fd.append('date_of_birth', profileData.date_of_birth);
    fd.append('bio', profileData.bio);
    fd.append('work_start_time', profileData.work_start_time);
    fd.append('work_end_time', profileData.work_end_time);
    fd.append('lunch_break_start', profileData.lunch_break_start);
    fd.append('lunch_break_end', profileData.lunch_break_end);
    fd.append('tea_break_start', profileData.tea_break_start);
    fd.append('tea_break_end', profileData.tea_break_end);
    if (profileData.profile_picture instanceof File) {
      fd.append('profile_picture', profileData.profile_picture);
    }
    const updated = await updateUserProfile(fd);
    if (updated.rescheduled_tasks_count !== undefined && updated.rescheduled_tasks_count > 0) {
      setMessage(`Schedule updated due to break change. ${updated.rescheduled_tasks_count} tasks have been automatically shifted to respect your new timings.`);
      // If tasks view is active, refresh the tasks to show updated times immediately
      if (activeTab === 'tasks') {
        handleLoadTasks();
      }
    } else {
      setMessage('Profile updated successfully!');
    }
    setProfileData(prev => ({
      ...prev,
      work_end_time: updated.working_schedule?.work_end_time || prev.work_end_time,
      lunch_break_end: updated.working_schedule?.lunch_break_end || prev.lunch_break_end,
      tea_break_end: updated.working_schedule?.tea_break_end || prev.tea_break_end,
      profile_picture_preview: updated.profile_picture ? (updated.profile_picture.startsWith('http') ? updated.profile_picture : `http://localhost:8000${updated.profile_picture}`) : prev.profile_picture_preview
    }));
  } catch (err) {
    if (err.response?.data && typeof err.response.data === 'object' && !err.response.data.error && !err.response.data.detail) {
        const errorMessages = Object.values(err.response.data).flat().join(' ');
        setError(errorMessages);
    } else {
        setError(err.response?.data?.error || err.response?.data?.detail || 'Failed to update profile');
    }
  } finally {
    setLoading(false);
  }
};
const handleRequestEmailChangeSubmit = async (e) => {
  e.preventDefault();
  setLoading(true);
  setError('');
  setMessage('');
  try {
    const res = await requestEmailChange(newEmail, emailChangePassword);
    setMessage(res.message || 'OTP sent to your new email address.');
    setEmailChangeStep('verify');
  } catch (err) {
    setError(err.response?.data?.error || err.response?.data?.detail || 'Failed to request email change');
  } finally {
    setLoading(false);
  }
};
const handleVerifyEmailChangeSubmit = async (e) => {
  e.preventDefault();
  setLoading(true);
  setError('');
  setMessage('');
  try {
    const otpCode = emailOtp.join('');
    const res = await verifyEmailChange(newEmail, otpCode);
    setMessage(res.message || 'Email updated successfully!');
    sessionStorage.setItem('email', newEmail);
    setEmailChangeStep('request');
    setEmailChangePassword('');
  } catch (err) {
    setError(err.response?.data?.error || err.response?.data?.detail || 'Failed to verify email change');
  } finally {
    setLoading(false);
  }
};
const handleChangePasswordSubmit = async (e) => {
  e.preventDefault();
  if (changePasswordData.new_password !== changePasswordData.confirm_password) {
    setError('Passwords do not match');
    return;
  }
  setLoading(true);
  setError('');
  setMessage('');
  try {
    await changePassword(sessionStorage.getItem('email'), changePasswordData.new_password);
    setMessage('Password changed successfully!');
    setChangePasswordData({ new_password: '', confirm_password: '' });
  } catch (err) {
    setError(err.response?.data?.error || err.response?.data?.detail || 'Failed to change password');
  } finally {
    setLoading(false);
  }
};
const handleRemoveMember = (memberId) => {
  modal.showConfirmation('Are you sure you want to remove this member?', async () => {
    setLoading(true);
    setError('');
    setMessage('');
    try {
      await removeMember(selectedOrg.id, memberId);
      modal.showSuccess('Member removed successfully!');
      const members = await getOrganizationMembers(selectedOrg.id);
      setOrgMembers(members);
    } catch (err) {
      modal.showError(err.response?.data?.error || err.response?.data?.detail || 'Failed to remove member');
    } finally {
      setLoading(false);
    }
  });
};
const handleChangeRole = async (memberId, role) => {
  setLoading(true);
  setError('');
  setMessage('');
  try {
    await changeMemberRole(selectedOrg.id, memberId, role);
    setMessage('Member role updated successfully!');
    const members = await getOrganizationMembers(selectedOrg.id);
    setOrgMembers(members);
    const currentEmail = sessionStorage.getItem('email');
    const updatedSelf = members.find(m => m.email.toLowerCase() === currentEmail?.toLowerCase());
    if (updatedSelf) {
      setSelectedOrg(prev => ({
        ...prev,
        my_status: { ...prev.my_status, role: updatedSelf.role }
      }));
    }
  } catch (err) {
    setError(err.response?.data?.error || err.response?.data?.detail || 'Failed to change role');
  } finally {
    setLoading(false);
  }
};
const handleChangePermissions = async (memberId, customPermissions) => {
  setLoading(true);
  setError('');
  setMessage('');
  try {
    await api.post(`/organizations/${selectedOrg.id}/change-permissions/`, {
      member_id: memberId,
      custom_permissions: customPermissions
    });
    setMessage('Permissions updated successfully!');
    const members = await getOrganizationMembers(selectedOrg.id);
    setOrgMembers(members);
    const updatedMember = members.find(m => m.id === memberId);
    if (updatedMember) {
      setSelectedPermissionMember(updatedMember);
    }
  } catch (err) {
    setError(err.response?.data?.error || err.response?.data?.detail || 'Failed to update permissions');
  } finally {
    setLoading(false);
  }
};
const handleEnterWorkspace = async (org, restoreTab = false) => {
  sessionStorage.setItem('selectedOrgId', org.id);
  setSelectedOrg(org);
  setLoading(true);
  setError(null);
  try {
    const isAdmin = org.my_status?.role === 'admin' || org.my_status?.role === 'owner';
    const [members, apps, requests, history, workspaceNotes, workspaceGoals, notifs, invites] = await Promise.all([
      getOrganizationMembers(org.id),
      api.get(`/dashboard/workspace-apps/?org_id=${org.id}`).then(res => res.data),
      isAdmin ? getJoinRequests(org.id).catch(() => []) : Promise.resolve([]),
      getWorkspaceHistory(org.id).catch(() => []),
      getNotes(org.id).catch(() => []),
      getGoals(org.id).catch(() => []),
      getNotifications(org.slug).catch(() => []),
      isAdmin ? getPendingInvitations(org.id).catch(() => []) : Promise.resolve([])
    ]);
    setOrgMembers(members);
    setWorkspaceApps(apps);
    setJoinRequests(requests);
    setWorkspaceHistory(history);
    setNotes(workspaceNotes);
    setGoals(workspaceGoals);
    setNotifications(notifs);
    setPendingInvites(invites);
    setView('dashboard');
    if (!restoreTab) {
      setActiveTab('overview');
    }
    setGoalsView('list');
    // Auto-subscribe to Web Push Notifications if supported
    enablePushNotifications();
  } catch (err) {
    console.error('Workspace load error:', err);
    setError(`Failed to load workspace: ${err.response?.data?.detail || err.message}`);
    if (err.response?.status === 403 || err.response?.status === 404) {
      setSelectedOrg(null);
      sessionStorage.removeItem('selectedOrgId');
      setView('onboarding');
      getOrganizations().then(orgs => setOrganizations(orgs)).catch(() => { });
    }
  } finally {
    setLoading(false);
  }
};
const handleManageRequest = async (requestId, action) => {
  setLoading(true);
  try {
    await manageJoinRequest(selectedOrg.id, requestId, action);
    setMessage(`Request ${action}ed successfully`);
    // Refresh data
    const [members, requests, history] = await Promise.all([
      getOrganizationMembers(selectedOrg.id),
      getJoinRequests(selectedOrg.id),
      getWorkspaceHistory(selectedOrg.id).catch(() => [])
    ]);
    setOrgMembers(members);
    setJoinRequests(requests);
    setWorkspaceHistory(history);
    setActiveJoinRequest(null);
  } catch (err) {
    setError('Failed to manage request');
  } finally {
    setLoading(false);
  }
};
// Notebook Note Handlers
const handleCreateNote = async () => {
  setSavingNote(true);
  try {
    const newNote = await createNote({
      organization: selectedOrg?.id,
      title: 'Untitled Note',
      content: ''
    });
    setNotes(prev => [newNote, ...prev]);
    setActiveNote(newNote);
    setNoteTitle(newNote.title);
    setNoteContent(newNote.content);
  } catch (err) {
    console.error('Failed to create note:', err);
  } finally {
    setSavingNote(false);
  }
};
const handleUpdateNote = async (updatedTitle, updatedContent) => {
  if (!activeNote) return;
  setSavingNote(true);
  try {
    const updated = await updateNote(activeNote.id, {
      title: updatedTitle,
      content: updatedContent
    });
    setNotes(prev => prev.map(n => n.id === updated.id ? updated : n));
    setActiveNote(updated);
  } catch (err) {
    console.error('Failed to update note:', err);
  } finally {
    setSavingNote(false);
  }
};
const handleDeleteNote = (noteId, e) => {
  if (e) e.stopPropagation();
  modal.showConfirmation('Are you sure you want to delete this note?', async () => {
    try {
      await deleteNote(noteId);
      setNotes(prev => prev.filter(n => n.id !== noteId));
      if (activeNote?.id === noteId) {
        setActiveNote(null);
        setNoteTitle('');
        setNoteContent('');
      }
    } catch (err) {
      console.error('Failed to delete note:', err);
    }
  });
};
const handleRestoreMember = async (memberId) => {
  setLoading(true);
  setError('');
  setMessage('');
  try {
    await restoreMember(selectedOrg.id, memberId);
    setMessage('Member restored successfully!');
    const [members, history] = await Promise.all([
      getOrganizationMembers(selectedOrg.id),
      getWorkspaceHistory(selectedOrg.id).catch(() => [])
    ]);
    setOrgMembers(members);
    setWorkspaceHistory(history);
  } catch (err) {
    setError(err.response?.data?.error || 'Failed to restore member');
  } finally {
    setLoading(false);
  }
};
const handleRestoreNote = async (noteId) => {
  setLoading(true);
  setError('');
  setMessage('');
  try {
    await restoreNote(noteId);
    setMessage('Note restored successfully!');
    const [workspaceNotes, history] = await Promise.all([
      getNotes(selectedOrg.id).catch(() => []),
      getWorkspaceHistory(selectedOrg.id).catch(() => [])
    ]);
    setNotes(workspaceNotes);
    setWorkspaceHistory(history);
  } catch (err) {
    setError(err.response?.data?.error || 'Failed to restore note');
  } finally {
    setLoading(false);
  }
};
// Leave Handlers
const handleLoadMembers = async () => {
  if (!selectedOrg) return;
  try {
    const members = await getOrganizationMembers(selectedOrg.id);
    setOrgMembers(members);
  } catch (err) {
    console.error('Failed to load organization members:', err);
  }
};
const handleLoadLeaves = async () => {
  if (!selectedOrg) return;
  setLeaveLoading(true);
  setLeaveError('');
  try {
    const myLeaves = await getUserLeaves(selectedOrg.id);
    setUserLeaves(myLeaves);
    const balances = await getLeaveBalances(selectedOrg.id);
    setLeaveBalances(balances);
    const isManager = selectedOrg?.my_status?.role === 'owner' || selectedOrg?.my_status?.role === 'admin';
    if (isManager) {
      const teamLeaves = await getAllLeaves(selectedOrg.id);
      setAllLeaves(teamLeaves);
    }
  } catch (err) {
    console.error('Failed to load leaves:', err);
    setLeaveError(err.response?.data?.detail || err.response?.data?.error || 'Failed to load leaves.');
  } finally {
    setLeaveLoading(false);
  }
};
const handleApplyLeave = async (e) => {
  e.preventDefault();
  if (!selectedOrg) return;
  setLeaveLoading(true);
  setLeaveError('');
  setLeaveSuccess('');
  try {
    let payload = leaveForm;
    if (leaveForm.attachment) {
      payload = new FormData();
      payload.append('organization', selectedOrg.id);
      payload.append('leave_type', leaveForm.leave_type);
      payload.append('start_date', leaveForm.start_date);
      payload.append('end_date', leaveForm.end_date);
      payload.append('reason', leaveForm.reason);
      payload.append('attachment', leaveForm.attachment);
    } else {
      payload = {
        organization: selectedOrg.id,
        leave_type: leaveForm.leave_type,
        start_date: leaveForm.start_date,
        end_date: leaveForm.end_date,
        reason: leaveForm.reason
      };
    }
    
    await applyLeave(payload);
    setLeaveSuccess('Leave request submitted successfully.');
    setLeaveForm({
      leave_type: 'Sick',
      start_date: '',
      end_date: '',
      reason: '',
      attachment: null
    });
    await handleLoadLeaves();
    await handleLoadMembers();
  } catch (err) {
    console.error('Failed to submit leave request:', err);
    const errorMsg = err.response?.data?.non_field_errors?.join(', ') ||
      err.response?.data?.detail ||
      err.response?.data?.error ||
      Object.values(err.response?.data || {}).flat().join(', ') ||
      'Failed to submit leave request.';
    setLeaveError(errorMsg);
  } finally {
    setLeaveLoading(false);
  }
};
const handleApproveLeave = async (leaveId) => {
  if (!selectedOrg) return;
  setLeaveLoading(true);
  setLeaveError('');
  setLeaveSuccess('');
  try {
    await approveLeave(leaveId);
    setLeaveSuccess('Leave request approved.');
    await handleLoadLeaves();
    await handleLoadMembers();
  } catch (err) {
    console.error('Failed to approve leave:', err);
    setLeaveError(err.response?.data?.detail || err.response?.data?.error || 'Failed to approve leave.');
  } finally {
    setLeaveLoading(false);
  }
};
const handleRejectLeave = async (leaveId) => {
  if (!selectedOrg) return;
  const reason = prompt("Enter rejection reason:");
  if (reason === null) return;
  
  setLeaveLoading(true);
  setLeaveError('');
  setLeaveSuccess('');
  try {
    await rejectLeave(leaveId, reason);
    setLeaveSuccess('Leave request rejected.');
    await handleLoadLeaves();
    await handleLoadMembers();
  } catch (err) {
    console.error('Failed to reject leave:', err);
    setLeaveError(err.response?.data?.detail || err.response?.data?.error || 'Failed to reject leave.');
  } finally {
    setLeaveLoading(false);
  }
};

const handleCancelLeave = async (leaveId) => {
  if (!selectedOrg) return;
  const reason = prompt("Enter reason for cancellation:");
  if (reason === null) return;

  setLeaveLoading(true);
  setLeaveError('');
  setLeaveSuccess('');
  try {
    await cancelLeave(leaveId, reason);
    setLeaveSuccess('Leave request cancelled successfully.');
    await handleLoadLeaves();
    await handleLoadMembers();
  } catch (err) {
    console.error('Failed to cancel leave:', err);
    setLeaveError(err.response?.data?.detail || err.response?.data?.error || 'Failed to cancel leave.');
  } finally {
    setLeaveLoading(false);
  }
};
// Goals CRUD Handlers
const handleLoadGoals = async () => {
  if (!selectedOrg) return;
  try {
    const workspaceGoals = await getOrgGoals(selectedOrg.slug);
    setGoals(workspaceGoals);
  } catch (err) {
    console.error('Failed to load goals:', err);
  }
};
const handleCreateGoal = async (e) => {
  e.preventDefault();
  setLoading(true);
  setError('');
  setMessage('');
  try {
    const createdGoal = await createOrgGoal(selectedOrg.slug, {
      title: newGoalData.title,
      description: newGoalData.description,
      owner: newGoalData.owner || null,
      priority: newGoalData.priority,
      visibility_type: newGoalData.visibility_type,
      visible_to: newGoalData.visible_to,
      sharing_option: newGoalData.sharing_option,
      assignees: newGoalData.assignees,
      shared_viewers: newGoalData.shared_viewers,
      parent: newGoalData.parent || null,
      depends_on: newGoalData.depends_on || null,
      timeframe: newGoalData.timeframe,
      template_type: selectedTemplateId ? 'custom' : newGoalData.template_type,
      is_shared_externally: newGoalData.is_shared_externally
    });
    if (selectedTemplateId) {
      try {
        await applyTemplateToGoal(selectedOrg.slug, selectedTemplateId, createdGoal.id);
        modal.showSuccess('Goal created and template applied successfully!');
        setSelectedTemplateId(null);
      } catch (templateErr) {
        console.error("Error applying template", templateErr);
        modal.showSuccess('Goal created, but failed to apply template folders/items.');
      }
    } else {
      modal.showSuccess('Goal created successfully!');
    }
    setNewGoalData({
      title: '',
      description: '',
      owner: '',
      priority: 'medium',
      visibility_type: 'specific',
      visible_to: [],
      sharing_option: 'specific',
      assignees: [],
      shared_viewers: [],
      parent: '',
      depends_on: '',
      timeframe: 'quarterly',
      template_type: 'none',
      is_shared_externally: false
    });
    setGoalsView('list');
    await handleLoadGoals();
  } catch (err) {
    modal.showError(err.response?.data?.error || err.response?.data?.detail || err.message || 'Failed to create goal');
  } finally {
    setLoading(false);
  }
};
const handleUpdateGoal = async (e) => {
  e.preventDefault();
  setLoading(true);
  setError('');
  setMessage('');
  try {
    await updateOrgGoal(selectedOrg.slug, activeGoal.id, {
      title: activeGoal.title,
      description: activeGoal.description,
      owner: activeGoal.owner?.id || activeGoal.owner || null,
      priority: activeGoal.priority,
      visibility_type: activeGoal.visibility_type,
      sharing_option: activeGoal.sharing_option,
      assignees: (activeGoal.assignees || []).map(a => a.id || a),
      shared_viewers: (activeGoal.shared_viewers || []).map(s => s.id || s),
      parent: activeGoal.parent || null,
      depends_on: activeGoal.depends_on || null,
      timeframe: activeGoal.timeframe || 'quarterly',
      template_type: activeGoal.template_type || 'none',
      is_shared_externally: activeGoal.is_shared_externally || false
    });
    setMessage('Goal updated successfully!');
    setGoalsView('detail');
    const updated = await getOrgGoalDetail(selectedOrg.slug, activeGoal.id);
    setActiveGoal(updated);
    await handleLoadGoals();
  } catch (err) {
    setError(err.response?.data?.error || err.response?.data?.detail || err.message || 'Failed to update goal');
  } finally {
    setLoading(false);
  }
};
const handleDeleteGoal = (goalId) => {
  modal.showConfirmation('Are you absolutely sure you want to delete this goal?', async () => {
    setLoading(true);
    setError('');
    setMessage('');
    try {
      await deleteOrgGoal(selectedOrg.slug, goalId);
      modal.showSuccess('Goal deleted successfully!');
      setGoalsView('list');
      setActiveGoal(null);
      await handleLoadGoals();
      if (selectedOrg) {
        const history = await getWorkspaceHistory(selectedOrg.id).catch(() => []);
        setWorkspaceHistory(history);
      }
    } catch (err) {
      modal.showError(err.response?.data?.error || 'Failed to delete goal');
    } finally {
      setLoading(false);
    }
  });
};
const handleRestoreGoal = async (goalId) => {
  setLoading(true);
  setError('');
  setMessage('');
  try {
    await restoreGoal(goalId);
    setMessage('Goal restored successfully!');
    await handleLoadGoals();
    if (selectedOrg) {
      const history = await getWorkspaceHistory(selectedOrg.id).catch(() => []);
      setWorkspaceHistory(history);
    }
  } catch (err) {
    setError(err.response?.data?.error || 'Failed to restore goal');
  } finally {
    setLoading(false);
  }
};
const handleCreateKr = async (e) => {
  e.preventDefault();
  setLoading(true);
  setError('');
  try {
    await createKeyResult(activeGoal.id, {
      title: krForm.title,
      target_value: krForm.target_value,
      current_value: krForm.current_value,
      unit: krForm.unit
    });
    setKrForm({ title: '', target_value: 100.0, current_value: 0.0, unit: '%' });
    setShowAddKr(false);
    const updated = await getGoalDetail(activeGoal.id);
    setActiveGoal(updated);
    await handleLoadGoals();
  } catch (err) {
    setError(err.response?.data?.error || 'Failed to add Key Result');
  } finally {
    setLoading(false);
  }
};
const handleCreateGoalTask = async (e) => {
  e.preventDefault();
  setLoading(true);
  setError('');
  try {
    const payload = {
      title: goalTaskForm.title,
      estimated_hours: goalTaskForm.estimated_hours || 0,
      estimated_minutes: goalTaskForm.estimated_minutes || 0,
      assignees: goalTaskForm.assignees,
      goal: activeGoal.id,
      organization: selectedOrg.id,
      issue_type: 'task',
      priority: 'medium',
      status: 'todo',
      visibility_type: 'specific',
    };
    const response = await createTask(payload);
    modal.showSuccess(formatTaskCreateSuccess(response));
    setGoalTaskForm({ title: '', estimated_hours: '', estimated_minutes: '', assignees: [] });
    setShowAddGoalTask(false);
    await handleLoadTasks();
  } catch (err) {
    modal.showError(err.response?.data?.error || err.response?.data?.detail || 'Failed to add task to Goal');
  } finally {
    setLoading(false);
  }
};
const handleUpdateKrValue = async (krId, newValue) => {
  try {
    await updateKeyResult(activeGoal.id, krId, { current_value: parseFloat(newValue) });
    const updated = await getGoalDetail(activeGoal.id);
    setActiveGoal(updated);
    await handleLoadGoals();
  } catch (err) {
    console.error('Failed to update Key Result value:', err);
  }
};
const handleDeleteKr = (krId) => {
  modal.showConfirmation('Are you sure you want to delete this Key Result?', async () => {
    setLoading(true);
    setError('');
    try {
      await deleteKeyResult(activeGoal.id, krId);
      const updated = await getGoalDetail(activeGoal.id);
      setActiveGoal(updated);
      await handleLoadGoals();
    } catch (err) {
      modal.showError(err.response?.data?.error || 'Failed to delete Key Result');
    } finally {
      setLoading(false);
    }
  });
};
const handleSendInvite = async (e) => {
  e.preventDefault();
  setLoading(true);
  try {
    // Normalize role for backend ('limited_member' and 'guest' map to 'member')
    let backendRole = inviteData.role;
    if (backendRole === 'limited_member' || backendRole === 'guest') {
      backendRole = 'member';
    }
    await inviteMember(selectedOrg.id, inviteData.email, backendRole, inviteData.message);
    setMessage(`Invitation sent to ${inviteData.email}`);
    setShowInviteModal(false);
    setShowRoleDropdown(false);
    setInviteData({ email: '', role: 'member', message: '' });
    const [history, invites] = await Promise.all([
      getWorkspaceHistory(selectedOrg.id).catch(() => []),
      getPendingInvitations(selectedOrg.id).catch(() => [])
    ]);
    setWorkspaceHistory(history);
    setPendingInvites(invites);
  } catch (err) {
    setError(err.response?.data?.error || 'Failed to send invitation');
  } finally {
    setLoading(false);
  }
};

const handleCancelInvitation = async (invitationId) => {
  setLoading(true);
  try {
    await cancelInvitation(selectedOrg.id, invitationId);
    setMessage('Invitation cancelled successfully');
    const [history, invites] = await Promise.all([
      getWorkspaceHistory(selectedOrg.id).catch(() => []),
      getPendingInvitations(selectedOrg.id).catch(() => [])
    ]);
    setWorkspaceHistory(history);
    setPendingInvites(invites);
  } catch (err) {
    setError(err.response?.data?.error || 'Failed to cancel invitation');
  } finally {
    setLoading(false);
  }
};

const handleAuthAction = async (e) => {
  e.preventDefault();
  setLoading(true);
  setError('');
  setMessage('');
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (view !== 'verify' && !emailRegex.test(formData.email)) {
    setError('Please enter a valid email address');
    setLoading(false);
    return;
  }
  if ((view === 'login' || view === 'register') && (!formData.password || formData.password.length < 6)) {
    setError('Password must be at least 6 characters long.');
    setLoading(false);
    return;
  }
  try {
    if (view === 'login') {
      await loginRequest(formData.email, formData.password);
      setPurpose('login');
      setView('verify');
    } else if (view === 'register') {
      await registerRequest({ email: formData.email, password: formData.password });
      setPurpose('registration');
      setView('verify');
    } else if (view === 'forgot') {
      await forgotPasswordRequest(formData.email);
      setPurpose('password_reset');
      setView('verify');
    } else if (view === 'verify') {
      const otpString = otp.join('');
      setOtp(['', '', '', '', '', '']); // Clear immediately after reading
      if (purpose === 'login') {
        const data = await verifyLoginOTP(formData.email, otpString);
        setAuthTokens(data.access, data.refresh);
        sessionStorage.setItem('email', formData.email);
        console.log('Login OTP verified, fetching workspaces...');
        setIsLoggedIn(true);
        if (data.requires_password_change) {
          sessionStorage.setItem('mustChangePassword', 'true');
          setMustChangePassword(true);
        }
        
        const pendingToken = sessionStorage.getItem('pending_invite_token');
        if (pendingToken) {
          sessionStorage.removeItem('pending_invite_token');
        }
        
        await fetchWorkspaces(data.access, false);
        setView('onboarding');
      } else if (purpose === 'registration') {
        await verifyRegistrationOTP(formData.email, otpString);
        setMessage('Account verified! You can now login.');
        setView('login');
        setOtp(['', '', '', '', '', '']);
      } else if (purpose === 'password_reset') {
        await resetPasswordVerify(formData.email, otpString, formData.password);
        setMessage('Password updated successfully! You can now login.');
        setView('login');
        setOtp(['', '', '', '', '', '']);
      }
    }
  } catch (err) {
    let errorMessage = err.response?.data?.error || err.response?.data?.detail || 'Authentication failed. Please try again.';
    // Friendly message mapping
    if (errorMessage.toLowerCase().includes('already exists') || errorMessage.toLowerCase().includes('unique')) {
      errorMessage = 'An account with this email already exists. Try logging in instead.';
    }
    setError(errorMessage);
    setOtp(['', '', '', '', '', '']);
  } finally {
    setLoading(false);
  }
};
const handleResend = async () => {
  setLoading(true);
  try {
    if (purpose === 'login') await resendLoginOTP(formData.email);
    else if (purpose === 'registration') await resendRegistrationOTP(formData.email);
    else if (purpose === 'password_reset') await forgotPasswordRequest(formData.email);
    setMessage('A new code has been sent.');
  } catch (err) {
    setError(err.response?.data?.error || 'Failed to resend OTP');
  } finally {
    setLoading(false);
  }
};
const handleLogout = async () => {
  try { await logout(); } catch (err) { }
  sessionStorage.clear();
  setAuthTokens(null);
  setIsLoggedIn(false);
  setView('login');
};
if (view === 'create_workspace') {
  return (
    <div style={{
      animation: 'slideInRight 0.4s ease-out forwards',
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#f8fafc'
    }}>
      <div style={{
        background: 'white',
        padding: '3.5rem',
        borderRadius: '24px',
        boxShadow: '0 20px 40px -10px rgba(0, 0, 0, 0.1)',
        width: '100%',
        maxWidth: '550px'
      }}>
        <h1 className="form-title" style={{ fontSize: '2.5rem', marginBottom: '0.5rem', textAlign: 'left' }}>Create Workspace</h1>
        <p className="form-subtitle" style={{ textAlign: 'left', marginBottom: '2.5rem', fontSize: '1.1rem' }}>Set up a new environment for your team to collaborate seamlessly.</p>
        <form onSubmit={handleCreateOrganization}>
          <div className="input-group" style={{ marginBottom: '2rem' }}>
            <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.9rem', marginBottom: '0.5rem' }}>WORKSPACE NAME</label>
            <input
              className="input-field"
              placeholder="e.g. Acme Corp"
              value={newOrgData.name}
              onChange={e => setNewOrgData({ ...newOrgData, name: e.target.value })}
              required
              style={{ background: '#f8fafc', border: '1px solid #cbd5e1', padding: '1rem', borderRadius: '12px', fontSize: '1.1rem', transition: 'border 0.2s, box-shadow 0.2s' }}
              onFocus={(e) => { e.target.style.border = '1px solid #6366f1'; e.target.style.boxShadow = '0 0 0 3px rgba(99,102,241,0.1)'; }}
              onBlur={(e) => { e.target.style.border = '1px solid #cbd5e1'; e.target.style.boxShadow = 'none'; }}
            />
          </div>
          <div className="input-group" style={{ marginBottom: '3rem' }}>
            <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.9rem', marginBottom: '0.5rem' }}>DESCRIPTION (OPTIONAL)</label>
            <textarea
              className="input-field"
              placeholder="What is this workspace for?"
              value={newOrgData.description}
              onChange={e => setNewOrgData({ ...newOrgData, description: e.target.value })}
              rows={3}
              style={{ background: '#f8fafc', border: '1px solid #cbd5e1', padding: '1rem', borderRadius: '12px', fontSize: '1.1rem', resize: 'vertical', transition: 'border 0.2s, box-shadow 0.2s' }}
              onFocus={(e) => { e.target.style.border = '1px solid #6366f1'; e.target.style.boxShadow = '0 0 0 3px rgba(99,102,241,0.1)'; }}
              onBlur={(e) => { e.target.style.border = '1px solid #cbd5e1'; e.target.style.boxShadow = 'none'; }}
            />
          </div>
          <div style={{ display: 'flex', gap: '1.5rem' }}>
            <button
              type="button"
              onClick={() => setView(sessionStorage.getItem('selectedOrgId') ? 'dashboard' : 'onboarding')}
              style={{ flex: 1, padding: '1rem', fontSize: '1.1rem', background: 'transparent', border: '2px solid #e2e8f0', color: '#64748b', borderRadius: '12px', fontWeight: 600, cursor: 'pointer', transition: 'background 0.2s' }}
              onMouseEnter={(e) => e.target.style.background = '#f1f5f9'}
              onMouseLeave={(e) => e.target.style.background = 'transparent'}
            >
              Go Back
            </button>
            <button
              type="submit"
              className="btn-primary"
              style={{ flex: 2, padding: '1rem', fontSize: '1.1rem', borderRadius: '12px', border: 'none', background: 'linear-gradient(135deg, #6366f1, #4f46e5)', boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)', transition: 'transform 0.2s, box-shadow 0.2s' }}
              disabled={loading}
              onMouseEnter={(e) => { e.target.style.transform = 'translateY(-2px)'; e.target.style.boxShadow = '0 6px 20px rgba(99, 102, 241, 0.5)'; }}
              onMouseLeave={(e) => { e.target.style.transform = 'none'; e.target.style.boxShadow = '0 4px 14px rgba(99, 102, 241, 0.4)'; }}
            >
              {loading ? <Loader2 className="animate-spin" /> : 'Launch Workspace'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
if (view === 'onboarding') {
  const activeOrgs = organizations.filter(org => org.is_active !== false);
  const deactivatedOrgs = organizations.filter(org => org.is_active === false);
  return (
    <div className="onboarding-container">
      <div className="onboarding-header">
        <h1 className="onboarding-title">Available Teams</h1>
        <div style={{ display: 'flex', gap: '1.25rem', alignItems: 'center' }}>
          <button className="social-btn" onClick={() => fetchWorkspaces(null, false)}>
            <RefreshCw size={16} /> Refresh
          </button>
          <button className="social-btn" onClick={handleLogout}>
            <LogOut size={16} /> Logout
          </button>
        </div>
      </div>
      <div className="search-container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'white', padding: '1rem 1.5rem', borderRadius: '16px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.02)', gap: '1.5rem', marginBottom: '2.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flex: 1, position: 'relative' }}>
          <Search size={18} style={{ color: '#94a3b8', position: 'absolute', left: '1rem' }} />
          <input
            className="input-field"
            placeholder="Search organizations..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            style={{ margin: 0, paddingLeft: '2.75rem', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px' }}
          />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', color: '#475569', fontSize: '0.9rem', fontWeight: 600, background: '#f1f5f9', padding: '0.4rem 0.8rem', borderRadius: '8px' }}>
          {activeOrgs.filter(org => org.name.toLowerCase().includes(searchQuery.toLowerCase())).length} teams found
        </div>
      </div>
      <button className="create-org-btn" onClick={() => setView('create_workspace')}>
        <span style={{ fontSize: '1.5rem' }}>+</span> Create New Workspace
      </button>
      {error && <div className="error-message">{error}</div>}
      {message && <div className="success-message">{message}</div>}
      <div className="org-list">
        {activeOrgs
          .filter(org => org.name.toLowerCase().includes(searchQuery.toLowerCase()))
          .sort((a, b) => {
            const aIsMember = a.my_status?.type === 'member' ? 1 : 0;
            const bIsMember = b.my_status?.type === 'member' ? 1 : 0;
            if (aIsMember !== bIsMember) {
              return bIsMember - aIsMember; // member first
            }
            const aIsPending = a.my_status?.status === 'pending' ? 1 : 0;
            const bIsPending = b.my_status?.status === 'pending' ? 1 : 0;
            if (aIsPending !== bIsPending) {
              return bIsPending - aIsPending; // pending second
            }
            return a.name.localeCompare(b.name); // alphabetically otherwise
          })
          .map(org => (
            <div key={org.id} className={`org-card ${org.my_status?.status === 'pending' ? 'pending' : ''}`} style={{ display: 'flex', gap: '1.25rem', alignItems: 'center', textAlign: 'left' }}>
              <div
                className="workspace-logo"
                style={{
                  width: '48px',
                  height: '48px',
                  flexShrink: 0,
                  fontSize: '1.4rem',
                  borderRadius: '12px',
                  background: org.logo ? 'transparent' : 'linear-gradient(135deg, #6366f1, #818cf8)'
                }}
              >
                {org.logo ? (
                  <img
                    src={getLogoUrl(org.logo)}
                    alt={org.name}
                    style={{ width: '100%', height: '100%', borderRadius: '12px', objectFit: 'cover' }}
                  />
                ) : (
                  org.name[0].toUpperCase()
                )}
              </div>
              <div className="org-info" style={{ flex: 1 }}>
                <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: '#0f172a' }}>{org.name}</h3>
                <div className="org-meta">
                  <span><UserIcon size={14} /> {org.created_by_email}</span>
                  <span><UserIcon size={14} /> {org.member_count} members</span>
                  <span><AudioWaveform size={14} /> Standard tier</span>
                </div>
                <p style={{ color: '#64748b', fontSize: '0.9rem' }}>{org.description || 'No description available'}</p>
                <div style={{ marginTop: '1.5rem' }}>
                  <label className="input-label" style={{ color: org.my_status ? '#64748b' : '#ef4444' }}>
                    Role : {org.my_status ? org.my_status.role : (selectedRoles[org.id] || 'Please select a role')}
                  </label>
                  {!org.my_status && (
                    <>
                      <div className="role-selector">
                        {['member', 'admin', 'owner'].map(role => (
                          <div
                            key={role}
                            className={`role-tag ${selectedRoles[org.id] === role ? 'selected' : ''}`}
                            onClick={() => setSelectedRoles({ ...selectedRoles, [org.id]: role })}
                          >
                            {role.charAt(0).toUpperCase() + role.slice(1)}
                          </div>
                        ))}
                      </div>
                      <button
                        className="btn-primary"
                        style={{ marginTop: '1.5rem' }}
                        onClick={() => {
                          const role = selectedRoles[org.id];
                          if (!role) {
                            setError('Please select a role first');
                            return;
                          }
                          setJoinOrgId(org.id);
                          setJoinMessage('');
                          setShowJoinModal(true);
                        }}
                        disabled={loading}
                      >
                        Send Join Request
                      </button>
                    </>
                  )}
                  {org.my_status?.type === 'invitation' && org.my_status?.status === 'pending' && (
                    <div style={{ marginTop: '1rem' }}>
                      <div className="invitation-details" style={{ background: '#f8fafc', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '1rem', fontSize: '0.85rem', color: '#475569' }}>
                        <div>Invited by: <strong>{org.my_status.invited_by || 'Workspace Owner'}</strong></div>
                        <div style={{ marginTop: '0.25rem' }}>Role: <span style={{ textTransform: 'capitalize', fontWeight: 600, color: '#6366f1' }}>{org.my_status.role}</span></div>
                      </div>
                      <button
                        className="btn-primary"
                        style={{ background: '#10b981', color: 'white', marginTop: 0 }}
                        onClick={() => handleAcceptInvitation(org, org.my_status.id)}
                        disabled={loading}
                      >
                        Accept Invitation
                      </button>
                    </div>
                  )}
                  {org.my_status?.type === 'request' && org.my_status?.status === 'pending' && (
                    <div className="btn-pending" style={{ display: 'inline-block', marginTop: '1.5rem' }}>Pending Request</div>
                  )}
                  {org.my_status?.type === 'member' && (
                    <button
                      className="btn-primary"
                      style={{ background: '#0f172a', marginTop: '1.5rem' }}
                      onClick={() => handleEnterWorkspace(org)}
                    >
                      Enter Workspace
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
      </div>
      {deactivatedOrgs.length > 0 && (
        <div className="deactivated-orgs-section" style={{ marginTop: '4rem', width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem', borderBottom: '1px solid #e2e8f0', paddingBottom: '0.75rem' }}>
            <Archive size={20} style={{ color: '#64748b' }} />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#475569', margin: 0 }}>Deactivated Workspaces</h2>
            <span style={{ fontSize: '0.8rem', color: '#94a3b8', background: '#f1f5f9', padding: '0.2rem 0.6rem', borderRadius: '12px', marginLeft: '0.5rem', fontWeight: 600 }}>
              {deactivatedOrgs.length}
            </span>
          </div>
          <p style={{ color: '#64748b', fontSize: '0.9rem', marginBottom: '2rem', textAlign: 'left' }}>
            These workspaces have been deactivated. Only the owner can view and reactivate them to restore access.
          </p>
          <div className="org-list" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {deactivatedOrgs
              .filter(org => org.name.toLowerCase().includes(searchQuery.toLowerCase()))
              .map(org => (
                <div
                  key={org.id}
                  className="org-card deactivated"
                  style={{
                    display: 'flex',
                    gap: '1.25rem',
                    alignItems: 'center',
                    textAlign: 'left',
                    background: '#f8fafc',
                    opacity: 0.85,
                    border: '1px dashed #cbd5e1',
                    padding: '1.5rem',
                    borderRadius: '16px'
                  }}
                >
                  <div
                    className="workspace-logo"
                    style={{
                      width: '48px',
                      height: '48px',
                      flexShrink: 0,
                      fontSize: '1.4rem',
                      borderRadius: '12px',
                      background: '#cbd5e1',
                      color: '#64748b',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 600
                    }}
                  >
                    {org.logo ? (
                      <img
                        src={getLogoUrl(org.logo)}
                        alt={org.name}
                        style={{ width: '100%', height: '100%', borderRadius: '12px', objectFit: 'cover', filter: 'grayscale(100%)' }}
                      />
                    ) : (
                      org.name[0].toUpperCase()
                    )}
                  </div>
                  <div className="org-info" style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: '#475569', textDecoration: 'line-through' }}>{org.name}</h3>
                      <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#e11d48', background: '#ffe4e6', padding: '0.15rem 0.5rem', borderRadius: '6px' }}>Deactivated</span>
                    </div>
                    <div className="org-meta" style={{ display: 'flex', gap: '1.25rem', marginTop: '0.5rem', color: '#64748b', fontSize: '0.875rem' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}><UserIcon size={14} /> Owner: {org.created_by_email}</span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}><UserIcon size={14} /> {org.member_count} members</span>
                    </div>
                    <p style={{ color: '#94a3b8', fontSize: '0.9rem', margin: '0.5rem 0 0 0' }}>{org.description || 'No description available'}</p>
                  </div>
                  <div style={{ display: 'flex', gap: '0.75rem' }}>
                    <button
                      className="btn-primary"
                      style={{
                        background: '#0284c7',
                        borderColor: '#0284c7',
                        color: 'white',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        padding: '0.5rem 1rem',
                        fontSize: '0.875rem',
                        cursor: 'pointer'
                      }}
                      onClick={() => handleReactivateOrg(org.id)}
                      disabled={loading}
                    >
                      {loading ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={14} />}
                      Reactivate Workspace
                    </button>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}
      {showJoinModal && (
        <div className="modal-overlay">
          <div className="modal-card">
            <h2 className="form-title" style={{ textAlign: 'left' }}>Join Workspace</h2>
            <p className="form-subtitle" style={{ textAlign: 'left' }}>Introduce yourself to the team. Send a message to request access.</p>
            <form onSubmit={(e) => {
              e.preventDefault();
              handleJoinRequest(joinOrgId);
            }}>
              <div className="input-group">
                <label className="input-label">Message (Optional)</label>
                <textarea
                  className="input-field"
                  placeholder="Hey there! I'd like to join this workspace to collaborate on..."
                  value={joinMessage}
                  onChange={e => setJoinMessage(e.target.value)}
                  rows={3}
                />
              </div>
              <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
                <button type="button" className="social-btn" onClick={() => setShowJoinModal(false)} style={{ flex: 1 }}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" style={{ flex: 1 }} disabled={loading}>
                  {loading ? <Loader2 className="animate-spin" /> : 'Send Request'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
if (view === 'collaborate') {
  return (
    <div className="onboarding-container" style={{ maxWidth: '1000px' }}>
      <div className="onboarding-header" style={{ marginBottom: '2rem' }}>
        <div>
          <button className="back-btn-smooth" onClick={() => setView('dashboard')} style={{ background: '#f8fafc', border: '1px solid #e2e8f0', padding: '0.4rem 0.8rem', borderRadius: '20px', color: '#475569', display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '1rem', cursor: 'pointer', fontSize: '0.85rem', fontWeight: 500, transition: 'all 0.2s', width: 'fit-content' }}>
            <ArrowLeft size={14} /> Back to Members
          </button>
          <h1 className="onboarding-title" style={{ fontSize: '2rem' }}>Discover Teams</h1>
          <p className="form-subtitle" style={{ textAlign: 'left', marginTop: '0.5rem' }}>Find and collaborate with organizations building great things.</p>
        </div>
      </div>
      <div className="search-container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'white', padding: '1rem 1.5rem', borderRadius: '16px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.02)', gap: '1.5rem', marginBottom: '2.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flex: 1, position: 'relative' }}>
          <Search size={18} style={{ color: '#94a3b8', position: 'absolute', left: '1rem' }} />
          <input
            className="input-field"
            placeholder="Search available organizations..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            style={{ margin: 0, paddingLeft: '2.75rem', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px' }}
          />
        </div>
      </div>
      <div className="org-list" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
        {organizations
          .filter(org => org.name.toLowerCase().includes(searchQuery.toLowerCase()) && org.my_status?.type !== 'member')
          .map(org => (
            <div key={org.id} className="org-card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', padding: '1.5rem', border: '1px solid #e2e8f0', borderRadius: '16px', background: 'white', transition: 'all 0.2s', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div className="workspace-logo" style={{ width: '48px', height: '48px', borderRadius: '12px', background: org.logo ? 'transparent' : 'linear-gradient(135deg, #6366f1, #818cf8)', fontSize: '1.4rem' }}>
                  {org.logo ? <img src={getLogoUrl(org.logo)} alt={org.name} style={{ width: '100%', height: '100%', borderRadius: '12px', objectFit: 'cover' }} /> : org.name[0].toUpperCase()}
                </div>
                <div>
                  <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: '#0f172a' }}>{org.name}</h3>
                  <div style={{ fontSize: '0.85rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.25rem' }}>
                    <Users size={14} /> {org.member_count} Members
                  </div>
                </div>
              </div>
              <p style={{ margin: 0, fontSize: '0.9rem', color: '#475569', lineHeight: 1.5, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden', height: '2.7rem' }}>
                {org.description || 'No description provided.'}
              </p>
              <div style={{ marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid #f1f5f9', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className={`status-chip ${org.my_status?.status === 'pending' ? 'pending' : ''}`} style={{ background: org.my_status?.status === 'pending' ? '#fef3c7' : '#f1f5f9', color: org.my_status?.status === 'pending' ? '#d97706' : '#64748b', padding: '0.25rem 0.75rem', borderRadius: '12px', fontSize: '0.8rem', fontWeight: 600 }}>
                  {org.my_status?.status === 'pending' ? 'Request Sent' : 'Public'}
                </span>
                <button
                  className="btn-primary"
                  onClick={() => { setCollaborateOrg(org); setView('collaborate-detail'); }}
                  style={{ padding: '0.5rem 1rem', fontSize: '0.9rem', width: 'auto' }}
                >
                  View Details
                </button>
              </div>
            </div>
          ))}
        {organizations.filter(org => org.name.toLowerCase().includes(searchQuery.toLowerCase()) && org.my_status?.type !== 'member').length === 0 && (
          <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '4rem 2rem', background: 'white', borderRadius: '16px', border: '1px dashed #cbd5e1' }}>
            <Search size={32} color="#cbd5e1" style={{ marginBottom: '1rem' }} />
            <h3 style={{ color: '#475569', fontSize: '1.2rem', marginBottom: '0.5rem' }}>No Organizations Found</h3>
            <p style={{ color: '#94a3b8' }}>Try adjusting your search query.</p>
          </div>
        )}
      </div>
    </div>
  );
}
if (view === 'collaborate-detail' && collaborateOrg) {
  return (
    <div className="onboarding-container" style={{ maxWidth: '800px' }}>
      <button className="back-btn-smooth" onClick={() => setView('collaborate')} style={{ background: '#f8fafc', border: '1px solid #e2e8f0', padding: '0.4rem 0.8rem', borderRadius: '20px', color: '#475569', display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '2rem', cursor: 'pointer', fontSize: '0.85rem', fontWeight: 500, transition: 'all 0.2s', width: 'fit-content' }}>
        <ArrowLeft size={14} /> Back to Discover
      </button>
      <div style={{ background: 'white', borderRadius: '24px', border: '1px solid #e2e8f0', padding: '3rem', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.05)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', marginBottom: '2rem' }}>
          <div className="workspace-logo" style={{ width: '80px', height: '80px', borderRadius: '20px', background: collaborateOrg.logo ? 'transparent' : 'linear-gradient(135deg, #6366f1, #818cf8)', fontSize: '2.5rem' }}>
            {collaborateOrg.logo ? <img src={getLogoUrl(collaborateOrg.logo)} alt={collaborateOrg.name} style={{ width: '100%', height: '100%', borderRadius: '20px', objectFit: 'cover' }} /> : collaborateOrg.name[0].toUpperCase()}
          </div>
          <div>
            <h1 style={{ fontSize: '2rem', fontWeight: 800, color: '#0f172a', margin: '0 0 0.5rem 0' }}>{collaborateOrg.name}</h1>
            <div style={{ display: 'flex', gap: '1rem', color: '#64748b', fontSize: '0.95rem' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Users size={16} /> {collaborateOrg.member_count} Members</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Target size={16} /> Public Workspace</span>
            </div>
          </div>
        </div>
        <div style={{ marginBottom: '3rem' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#1e293b', marginBottom: '1rem' }}>About this Organization</h3>
          <p style={{ fontSize: '1rem', color: '#475569', lineHeight: 1.7 }}>
            {collaborateOrg.description || "This organization hasn't provided a description yet."}
          </p>
        </div>
        <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '16px', padding: '2rem' }}>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#1e293b', marginBottom: '0.5rem' }}>Request to Join</h3>
          <p style={{ color: '#64748b', marginBottom: '1.5rem' }}>Send a collaboration request to the workspace administrators.</p>
          {error && <div className="error-message" style={{ marginBottom: '1rem' }}>{error}</div>}
          {message && <div className="success-message" style={{ marginBottom: '1rem' }}>{message}</div>}
          <form onSubmit={async (e) => {
            e.preventDefault();
            setLoading(true);
            setError('');
            setMessage('');
            try {
              const role = selectedRoles[collaborateOrg.id] || 'member';
              await sendJoinRequest(collaborateOrg.id, role, joinMessage);
              setMessage('Join request sent successfully! An administrator will review it soon.');
              setJoinMessage('');
              await fetchWorkspaces(null, false);
              // Update local collaborateOrg to show pending status
              setCollaborateOrg(prev => ({ ...prev, my_status: { status: 'pending' } }));
            } catch (err) {
              setError(err.response?.data?.error || 'Failed to send request');
            } finally {
              setLoading(false);
            }
          }}>
            <div className="input-group" style={{ marginBottom: '1.5rem' }}>
              <label className="input-label">Requested Role</label>
              <div style={{ display: 'flex', gap: '1rem' }}>
                {['member', 'admin'].map(role => (
                  <div
                    key={role}
                    className={`role-badge ${selectedRoles[collaborateOrg.id] === role || (!selectedRoles[collaborateOrg.id] && role === 'member') ? 'active' : ''}`}
                    onClick={() => setSelectedRoles(prev => ({ ...prev, [collaborateOrg.id]: role }))}
                    style={{ cursor: 'pointer', padding: '0.75rem 1.5rem', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '0.9rem', fontWeight: 600, color: '#475569', transition: 'all 0.2s', ...(selectedRoles[collaborateOrg.id] === role || (!selectedRoles[collaborateOrg.id] && role === 'member') ? { background: '#ebf4ff', borderColor: '#3b82f6', color: '#1d4ed8' } : {}) }}
                  >
                    {role.charAt(0).toUpperCase() + role.slice(1)}
                  </div>
                ))}
              </div>
            </div>
            <div className="input-group" style={{ marginBottom: '2rem' }}>
              <label className="input-label">Message to Admins (Optional)</label>
              <textarea
                className="input-field"
                placeholder="Hey there! I'd like to join this workspace to collaborate on..."
                value={joinMessage}
                onChange={e => setJoinMessage(e.target.value)}
                rows={4}
                style={{ resize: 'vertical' }}
              />
            </div>
            <button
              type="submit"
              className="btn-primary"
              disabled={loading || collaborateOrg.my_status?.status === 'pending'}
              style={{ width: '100%', padding: '1rem', fontSize: '1.1rem', background: collaborateOrg.my_status?.status === 'pending' ? '#cbd5e1' : 'linear-gradient(135deg, #6366f1, #818cf8)' }}
            >
              {loading ? <Loader2 className="animate-spin" /> : collaborateOrg.my_status?.status === 'pending' ? 'Request Pending' : 'Send Join Request'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
if (view === 'deactivate-workspace') {
  return (
    <div className="confirmation-page-container">
      <div className="confirmation-page-card">
        <div className="confirmation-page-header">
          <AlertCircle size={28} color="#475569" />
          <h1 className="confirmation-page-title">Deactivate Workspace</h1>
        </div>
        {confirmModalError && (
          <div className="error-message" style={{ marginBottom: '1.5rem', padding: '0.75rem', borderRadius: '8px', background: '#fef2f2', color: '#b91c1c', fontSize: '0.85rem' }}>
            {confirmModalError}
          </div>
        )}
        <p className="confirmation-page-description">
          You are about to deactivate the workspace <strong>{selectedOrg?.name}</strong>. Please review the consequences of this action below.
        </p>
        <div className="confirmation-impact-box deactivate">
          <h3 className="confirmation-impact-title deactivate">What happens after deactivation?</h3>
          <ul className="confirmation-actions-list">
            <li>The workspace will be hidden from members' navigation lists immediately.</li>
            <li>Active tasks, goals, templates, and group chats will be paused/archived.</li>
            <li>No data is deleted. The owner can reactivate the workspace at any time.</li>
          </ul>
        </div>
        <div className="confirmation-input-section">
          <label className="confirmation-input-label">
            Enter the workspace name <strong>{selectedOrg?.name}</strong> to confirm deactivation:
          </label>
          <input
            type="text"
            className={`confirm-input-premium ${confirmInput === selectedOrg?.name ? 'valid' : ''}`}
            placeholder="Type workspace name..."
            value={confirmInput}
            onChange={(e) => setConfirmInput(e.target.value)}
            style={{ width: '100%' }}
          />
        </div>
        <div className="confirmation-footer-btn-group">
          <button
            type="button"
            className="btn-deactivate-premium"
            onClick={() => {
              setView('dashboard');
              setActiveTab('settings');
              setConfirmInput('');
              setConfirmModalError('');
            }}
            style={{ padding: '0.75rem 1.75rem' }}
          >
            Cancel & Go Back
          </button>
          <button
            type="button"
            className="btn-deactivate-premium"
            disabled={loading || confirmInput !== selectedOrg?.name}
            onClick={handleDeactivateOrg}
            style={{
              padding: '0.75rem 1.75rem',
              ...(confirmInput === selectedOrg?.name ? { backgroundColor: '#475569', color: '#ffffff', borderColor: '#475569' } : {})
            }}
          >
            {loading ? <Loader2 className="animate-spin" /> : 'Deactivate Workspace'}
          </button>
        </div>
      </div>
    </div>
  );
}
if (view === 'delete-workspace') {
  return (
    <div className="confirmation-page-container">
      <div className="confirmation-page-card">
        <div className="confirmation-page-header">
          <AlertCircle size={28} color="#ef4444" />
          <h1 className="confirmation-page-title" style={{ color: '#ef4444' }}>Delete Workspace</h1>
        </div>
        {confirmModalError && (
          <div className="error-message" style={{ marginBottom: '1.5rem', padding: '0.75rem', borderRadius: '8px', background: '#fef2f2', color: '#b91c1c', fontSize: '0.85rem' }}>
            {confirmModalError}
          </div>
        )}
        <p className="confirmation-page-description">
          You are initiating a permanent deletion of the workspace <strong>{selectedOrg?.name}</strong>. This action is destructive and cannot be undone.
        </p>
        <div className="confirmation-impact-box">
          <h3 className="confirmation-impact-title">Irreversible Consequences</h3>
          <ul className="confirmation-actions-list" style={{ color: '#991b1b' }}>
            <li>All workspace users and admins will immediately lose access.</li>
            <li>All active and archived tasks, goals, notes, and messages will be permanently purged.</li>
            <li>Any file attachments, documents, or data history will be completely erased.</li>
          </ul>
        </div>
        <div className="confirmation-input-section">
          <label className="confirmation-input-label">
            Enter the workspace name <strong>{selectedOrg?.name}</strong> to confirm permanent deletion:
          </label>
          <input
            type="text"
            className={`confirm-input-premium ${confirmInput === selectedOrg?.name ? 'valid' : ''}`}
            placeholder="Type workspace name..."
            value={confirmInput}
            onChange={(e) => setConfirmInput(e.target.value)}
            style={{ width: '100%' }}
          />
        </div>
        <div className="confirmation-footer-btn-group">
          <button
            type="button"
            className="btn-deactivate-premium"
            onClick={() => {
              setView('dashboard');
              setActiveTab('settings');
              setConfirmInput('');
              setConfirmModalError('');
            }}
            style={{ padding: '0.75rem 1.75rem' }}
          >
            Cancel & Go Back
          </button>
          <button
            type="button"
            className="btn-delete-premium"
            disabled={loading || confirmInput !== selectedOrg?.name}
            onClick={handlePermanentDeleteOrg}
            style={{ padding: '0.75rem 1.75rem' }}
          >
            {loading ? <Loader2 className="animate-spin" /> : 'Permanently Delete Workspace'}
          </button>
        </div>
      </div>
    </div>
  );
}
if (view === 'dashboard') {
  return (
    <div className="dashboard-layout">
      {/* Slim Icon Sidebar */}
      <aside className="sidebar-slim">
        {/* Workspace Logo / Switcher */}
        <div
          className="slim-logo-btn"
          onClick={(e) => { e.stopPropagation(); setShowWorkspaceDropdown(!showWorkspaceDropdown); }}
          title={selectedOrg?.name}
        >
          <div
            className="workspace-logo-slim"
            style={{ background: selectedOrg?.logo ? 'transparent' : 'linear-gradient(135deg, #6366f1, #818cf8)' }}
          >
            {selectedOrg?.logo ? (
              <img src={getLogoUrl(selectedOrg.logo)} alt={selectedOrg.name} style={{ width: '100%', height: '100%', borderRadius: '8px', objectFit: 'cover' }} />
            ) : (
              selectedOrg?.name?.[0].toUpperCase()
            )}
          </div>
          {showWorkspaceDropdown && (
            <div className="workspace-dropdown-popover" style={{ left: '68px', top: 0, right: 'auto', width: '220px' }} onClick={e => e.stopPropagation()}>
              <div className="dropdown-title">Switch Workspace</div>
              <div className="dropdown-divider" />
              <div className="dropdown-list">
                {organizations.filter(org => org.my_status?.type === 'member').map(org => (
                  <div
                    key={org.id}
                    className={`dropdown-item ${org.id === selectedOrg?.id ? 'active' : ''}`}
                    onClick={() => { setShowWorkspaceDropdown(false); handleEnterWorkspace(org); }}
                  >
                    <div className="item-logo" style={{ background: org.logo ? 'transparent' : 'linear-gradient(135deg, #6366f1, #3b82f6)' }}>
                      {org.logo ? <img src={getLogoUrl(org.logo)} alt={org.name} style={{ width: '100%', height: '100%', borderRadius: '6px', objectFit: 'cover' }} /> : org.name[0].toUpperCase()}
                    </div>
                    <div className="item-details" style={{ flex: 1 }}>
                      <div className="item-name">{org.name}</div>
                      <div className="item-role">{org.my_status?.role}</div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="dropdown-divider" />
              <div className="dropdown-action" onClick={() => { setShowWorkspaceDropdown(false); setView('create_workspace'); }}>
                <Plus size={16} /> Create Workspace
              </div>
            </div>
          )}
        </div>
        <div className="slim-divider" />
        {/* Nav Icons */}
        <nav className="slim-nav">
          <SlimNavItem icon={<LayoutDashboard size={16} />} label="Overview" active={activeTab === 'overview'} onClick={() => setActiveTab('overview')} />
          <SlimNavItem icon={<Target size={16} />} label="All Goals" active={activeTab === 'goals'} onClick={() => { setActiveTab('goals'); setGoalsView('list'); handleLoadGoals(); }} />
          <SlimNavItem icon={<ListTodo size={16} />} label="Tasks" active={activeTab === 'tasks'} onClick={() => { setActiveTab('tasks'); setTasksView('list'); handleLoadTasks(); }} />
          <SlimNavItem icon={<Hourglass size={16} />} label="Pending Queue" active={activeTab === 'pending_queue'} onClick={() => { setActiveTab('pending_queue'); }} />
          <SlimNavItem icon={<MessageSquare size={16} />} label="Chat" active={activeTab === 'chat'} onClick={() => setActiveTab('chat')} />
          <SlimNavItem icon={<Calendar size={16} />} label="Calendar" active={activeTab === 'calendar'} onClick={() => setActiveTab('calendar')} />
          <SlimNavItem icon={<Coffee size={16} />} label="Leaves" active={activeTab === 'leaves'} onClick={() => { setActiveTab('leaves'); }} />
          <SlimNavItem icon={<Folder size={16} />} label="Templates" active={activeTab === 'templates'} onClick={() => setActiveTab('templates')} />
          <SlimNavItem icon={<Key size={16} />} label="Permissions" active={activeTab === 'permissions'} onClick={() => setActiveTab('permissions')} badge={(selectedOrg?.my_status?.role === 'owner' || selectedOrg?.my_status?.role === 'admin') ? (joinRequests.length || 0) : 0} />
          <SlimNavItem icon={<Users size={16} />} label="Members" active={activeTab === 'members'} onClick={() => setActiveTab('members')} />
          <SlimNavItem icon={<UserIcon size={16} />} label="Profile" active={activeTab === 'profile'} onClick={() => setActiveTab('profile')} />
          <SlimNavItem icon={<History size={16} />} label="History & Notifications" active={activeTab === 'history'} onClick={() => { setActiveTab('history'); setSelectedHistoryLog(null); }} badge={notifications.filter(n => !n.is_read).length} />
          {(selectedOrg?.my_status?.role === 'owner' || selectedOrg?.my_status?.role === 'admin') && (
            <SlimNavItem icon={<Settings size={16} />} label="Settings" active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} />
          )}
        </nav>
        {/* Footer Icons */}
        <div className="slim-footer">
          <SlimNavItem icon={<ArrowLeft size={16} />} label="Back to Teams" onClick={() => setView('onboarding')} />
          <SlimNavItem icon={<LogOut size={16} />} label="Logout" onClick={handleLogout} />
        </div>
      </aside>
      {/* Main Content */}
      <main className="main-content">
        <header className="main-header">
          <div className="header-left">
            <h2 className="page-title">
              {activeTab === 'overview' && 'Overview'}
              {activeTab === 'goals' && 'Goals'}
              {activeTab === 'tasks' && 'Task Management'}
              {activeTab === 'pending_queue' && 'Pending Queue'}
              {activeTab === 'permissions' && 'Permissions'}
              {activeTab === 'members' && 'Members'}
              {activeTab === 'profile' && 'User Profile'}
              {activeTab === 'calendar' && 'Calendar'}
              {activeTab === 'templates' && 'Templates'}
              {activeTab === 'history' && 'History'}
              {activeTab === 'leaves' && 'Leave Management'}
              {activeTab === 'settings' && 'Settings'}
            </h2>
            <span style={{ fontSize: '0.8rem', color: '#94a3b8', marginLeft: '0.75rem', fontWeight: 500 }}>
              {selectedOrg?.name}
            </span>
          </div>
          <div className="header-right">
            {/* Live date & time with Calendar Popover */}
            <div
              className="datetime-wrapper"
              style={{ position: 'relative' }}
              onMouseEnter={() => { setShowCalendarPopover(true); setShowNotifications(false); }}
              onMouseLeave={() => setShowCalendarPopover(false)}
            >
              <div
                className="header-datetime"
                onClick={(e) => { e.stopPropagation(); setShowCalendarPopover(!showCalendarPopover); setShowNotifications(false); }}
                style={{ cursor: 'pointer' }}
              >
                <Clock size={13} style={{ color: '#94a3b8' }} />
                <span className="header-time">{liveTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })}</span>
                <span className="header-date-sep">·</span>
                <span className="header-date">{liveTime.toLocaleDateString([], { weekday: 'short', day: '2-digit', month: 'short' })}</span>
              </div>
              {showCalendarPopover && (() => {
                const now = liveTime;
                const year = now.getFullYear();
                const month = now.getMonth();
                const today = now.getDate();
                const firstDay = new Date(year, month, 1).getDay();
                const daysInMonth = new Date(year, month + 1, 0).getDate();
                const monthName = now.toLocaleDateString([], { month: 'long', year: 'numeric' });
                const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
                const cells = [];
                for (let i = 0; i < firstDay; i++) cells.push(null);
                for (let d = 1; d <= daysInMonth; d++) cells.push(d);
                return (
                  <div className="calendar-popover" onClick={(e) => e.stopPropagation()} style={{ position: 'absolute', top: '115%', right: 0, background: 'white', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '0.75rem', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)', zIndex: 100, width: '240px' }}>
                    <div className="calendar-popover-header" style={{ fontFamily: 'Outfit, sans-serif', fontWeight: 600, fontSize: '0.85rem', color: '#0f172a', textAlign: 'center', marginBottom: '0.5rem', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.25rem' }}>
                      {monthName}
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '2px', textAlign: 'center', marginBottom: '0.25rem' }}>
                      {dayNames.map(d => (
                        <div key={d} style={{ fontSize: '0.65rem', fontWeight: 700, color: '#94a3b8' }}>{d}</div>
                      ))}
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '2px' }}>
                      {cells.map((day, idx) => (
                        <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '28px' }}>
                          {day && (
                            <div className={`calendar-day-cell ${day === today ? 'today' : 'normal'}`} style={{ width: '24px', height: '24px', fontSize: '0.75rem' }}>
                              {day}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })()}
            </div>
            {/* User email chip + role badge */}
            <NotificationDropdown />
            <div className="header-user-chip" title={sessionStorage.getItem('email')}>
              <span className="header-user-email">{sessionStorage.getItem('email')}</span>
            </div>
            <div className={`header-role-badge role-badge-${selectedOrg?.my_status?.role}`}>
              {selectedOrg?.my_status?.role || 'Member'}
            </div>
            <div className="user-profile">
              <div className="avatar">{sessionStorage.getItem('email')?.[0].toUpperCase()}</div>
            </div>
          </div>
        </header>
        <div className="content-scroll">
          {activeTab === 'overview' && (
            <Dashboard
              activeOrg={selectedOrg}
              onNavigate={handleDashboardNavigation}
              joinRequestsCount={joinRequests?.length || 0}
            />
          )}
          {activeTab === 'chat' && (() => {
            return <ChatLayout activeOrg={selectedOrg} initialRoomId={initialChatRoomId} />;
          })()}
          {activeTab === 'history' && (() => {
            const logs = workspaceHistory.filter(item => item.status !== 'deleted');
            const recoveryItems = workspaceHistory.filter(item => item.status === 'deleted');
            if (selectedHistoryLog) {
              return (
                <div style={{ maxWidth: 860, margin: '0 auto' }}>
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1.5rem', gap: '1rem' }}>
                    <button
                      onClick={() => setSelectedHistoryLog(null)}
                      style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', fontWeight: 600, padding: 0 }}
                    >
                      <ArrowLeft size={18} /> Back to History
                    </button>
                  </div>
                  <div style={{ background: 'white', borderRadius: '16px', padding: '2rem', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)', border: '1px solid #e2e8f0' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem', paddingBottom: '1.5rem', borderBottom: '1px solid #e2e8f0' }}>
                      <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: '#eef2ff', color: '#6366f1', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <History size={24} />
                      </div>
                      <div>
                        <h2 style={{ margin: '0 0 0.25rem 0', color: '#0f172a', fontSize: '1.25rem' }}>Event Log Details</h2>
                        <p style={{ margin: 0, color: '#64748b', fontSize: '0.9rem' }}>Detailed view of the selected workspace event</p>
                      </div>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                      <div>
                        <p style={{ margin: '0 0 0.5rem 0', color: '#64748b', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>User / Target</p>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: '#f1f5f9', color: '#475569', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600, fontSize: '0.85rem' }}>
                            {(selectedHistoryLog.email || selectedHistoryLog.title || 'U')[0].toUpperCase()}
                          </div>
                          <p style={{ margin: 0, color: '#0f172a', fontWeight: 600, fontSize: '1rem' }}>{selectedHistoryLog.email || selectedHistoryLog.title}</p>
                        </div>
                      </div>
                      <div>
                        <p style={{ margin: '0 0 0.5rem 0', color: '#64748b', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Timestamp</p>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#334155', fontWeight: 500 }}>
                          <Clock size={16} style={{ color: '#94a3b8' }} />
                          {new Date(selectedHistoryLog.timestamp).toLocaleDateString()} at {new Date(selectedHistoryLog.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                      <div>
                        <p style={{ margin: '0 0 0.5rem 0', color: '#64748b', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Status / Action</p>
                        <span style={{
                          display: 'inline-flex', alignItems: 'center', padding: '0.35rem 0.85rem', borderRadius: '8px', fontSize: '0.85rem', fontWeight: 600, textTransform: 'capitalize',
                          background: (selectedHistoryLog.status === 'accepted' || selectedHistoryLog.status === 'approved') ? '#ecfdf5' : selectedHistoryLog.status === 'pending' ? '#fff7ed' : '#fef2f2',
                          color: (selectedHistoryLog.status === 'accepted' || selectedHistoryLog.status === 'approved') ? '#059669' : selectedHistoryLog.status === 'pending' ? '#c2410c' : '#ef4444'
                        }}>
                          {selectedHistoryLog.status || selectedHistoryLog.type.replace('_', ' ')}
                        </span>
                      </div>
                      <div>
                        <p style={{ margin: '0 0 0.5rem 0', color: '#64748b', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Type</p>
                        <span style={{ display: 'inline-flex', padding: '0.35rem 0.85rem', borderRadius: '8px', fontSize: '0.85rem', fontWeight: 600, background: selectedHistoryLog.type === 'invitation' ? '#eef2ff' : '#f0fdf4', color: selectedHistoryLog.type === 'invitation' ? '#6366f1' : '#16a34a', textTransform: 'uppercase' }}>
                          {selectedHistoryLog.type.replace('_', ' ')}
                        </span>
                      </div>
                      {selectedHistoryLog.role && (
                        <div>
                          <p style={{ margin: '0 0 0.5rem 0', color: '#64748b', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Role Assigned</p>
                          <span style={{ display: 'inline-flex', padding: '0.35rem 0.85rem', borderRadius: '8px', fontSize: '0.85rem', fontWeight: 600, background: '#f8fafc', color: '#475569', border: '1px solid #e2e8f0', textTransform: 'capitalize' }}>
                            {selectedHistoryLog.role}
                          </span>
                        </div>
                      )}
                      {selectedHistoryLog.invited_by && (
                        <div>
                          <p style={{ margin: '0 0 0.5rem 0', color: '#64748b', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Invited By</p>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#334155', fontWeight: 500 }}>
                            <UserIcon size={16} style={{ color: '#94a3b8' }} />
                            {selectedHistoryLog.invited_by}
                          </div>
                        </div>
                      )}
                      {selectedHistoryLog.message && (
                        <div style={{ gridColumn: '1 / -1', marginTop: '0.5rem' }}>
                          <p style={{ margin: '0 0 0.75rem 0', color: '#64748b', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Attached Message</p>
                          <div style={{ background: '#f8fafc', padding: '1.25rem', borderRadius: '12px', border: '1px solid #e2e8f0', display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                            <MessageSquare size={20} style={{ color: '#94a3b8', flexShrink: 0, marginTop: '0.1rem' }} />
                            <p style={{ margin: 0, color: '#334155', fontSize: '0.95rem', lineHeight: 1.6, fontStyle: 'italic' }}>"{selectedHistoryLog.message}"</p>
                          </div>
                        </div>
                      )}
                    </div>
                    {selectedHistoryLog.type === 'join_request' && selectedHistoryLog.status === 'pending' && (
                      <div style={{ display: 'flex', gap: '0.75rem', marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid #e2e8f0', gridColumn: '1 / -1' }}>
                        <button disabled={loading}
                          onClick={async () => {
                            setLoading(true);
                            try {
                              await manageJoinRequest(selectedOrg.id, selectedHistoryLog.id, 'approve');
                              setMessage(`✅ ${selectedHistoryLog.email}'s request approved. Email sent.`);
                              const [history, reqs] = await Promise.all([
                                getWorkspaceHistory(selectedOrg.id).catch(() => []),
                                getJoinRequests(selectedOrg.id).catch(() => [])
                              ]);
                              setWorkspaceHistory(history);
                              setJoinRequests(reqs);
                              setSelectedHistoryLog(null);
                            } catch (err) { setError('Failed to approve request.'); }
                            finally { setLoading(false); }
                          }}
                          style={{ padding: '0.6rem 1.5rem', background: '#22c55e', color: 'white', border: 'none', borderRadius: '8px', fontSize: '0.9rem', fontWeight: 600, cursor: 'pointer', transition: 'all 0.15s' }}
                          onMouseOver={e => e.currentTarget.style.background = '#16a34a'}
                          onMouseOut={e => e.currentTarget.style.background = '#22c55e'}
                        >✓ Approve</button>
                        <button disabled={loading}
                          onClick={async () => {
                            setLoading(true);
                            try {
                              await manageJoinRequest(selectedOrg.id, selectedHistoryLog.id, 'deny');
                              setMessage(`❌ ${selectedHistoryLog.email}'s request denied. Email sent.`);
                              const [history, reqs] = await Promise.all([
                                getWorkspaceHistory(selectedOrg.id).catch(() => []),
                                getJoinRequests(selectedOrg.id).catch(() => [])
                              ]);
                              setWorkspaceHistory(history);
                              setJoinRequests(reqs);
                              setSelectedHistoryLog(null);
                            } catch (err) { setError('Failed to deny request.'); }
                            finally { setLoading(false); }
                          }}
                          style={{ padding: '0.6rem 1.5rem', background: '#ef4444', color: 'white', border: 'none', borderRadius: '8px', fontSize: '0.9rem', fontWeight: 600, cursor: 'pointer', transition: 'all 0.15s' }}
                          onMouseOver={e => e.currentTarget.style.background = '#dc2626'}
                          onMouseOut={e => e.currentTarget.style.background = '#ef4444'}
                        >✕ Deny</button>
                      </div>
                    )}
                    {selectedHistoryLog.type === 'invitation' && selectedHistoryLog.status === 'pending' && selectedHistoryLog.email.toLowerCase() === sessionStorage.getItem('email')?.toLowerCase() && (
                      <div style={{ display: 'flex', gap: '0.75rem', marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid #e2e8f0', gridColumn: '1 / -1' }}>
                        <button disabled={loading}
                          onClick={async () => {
                            setLoading(true);
                            try {
                              await acceptInvitation(selectedHistoryLog.id);
                              setMessage(`✅ Invitation accepted for ${selectedHistoryLog.email}. Email sent.`);
                              const history = await getWorkspaceHistory(selectedOrg.id).catch(() => []);
                              setWorkspaceHistory(history);
                              setSelectedHistoryLog(null);
                            } catch (err) { setError(err.response?.data?.error || 'Failed to accept invitation.'); }
                            finally { setLoading(false); }
                          }}
                          style={{ padding: '0.6rem 1.5rem', background: '#6366f1', color: 'white', border: 'none', borderRadius: '8px', fontSize: '0.9rem', fontWeight: 600, cursor: 'pointer', transition: 'all 0.15s' }}
                          onMouseOver={e => e.currentTarget.style.background = '#4f46e5'}
                          onMouseOut={e => e.currentTarget.style.background = '#6366f1'}
                        >✓ Accept</button>
                        <button disabled={loading}
                          onClick={async () => {
                            setLoading(true);
                            try {
                              await declineInvitation(selectedHistoryLog.id);
                              setMessage(`Invitation declined for ${selectedHistoryLog.email}. Email sent.`);
                              const history = await getWorkspaceHistory(selectedOrg.id).catch(() => []);
                              setWorkspaceHistory(history);
                              setSelectedHistoryLog(null);
                            } catch (err) { setError(err.response?.data?.error || 'Failed to decline invitation.'); }
                            finally { setLoading(false); }
                          }}
                          style={{ padding: '0.6rem 1.5rem', background: '#94a3b8', color: 'white', border: 'none', borderRadius: '8px', fontSize: '0.9rem', fontWeight: 600, cursor: 'pointer', transition: 'all 0.15s' }}
                          onMouseOver={e => e.currentTarget.style.background = '#64748b'}
                          onMouseOut={e => e.currentTarget.style.background = '#94a3b8'}
                        >✕ Decline</button>
                      </div>
                    )}
                  </div>
                </div>
              );
            }
            return (
              <div style={{ maxWidth: 860, margin: '0 auto' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                  <div>
                    <h2 className="section-title-premium" style={{ marginBottom: '0.25rem' }}>Workspace Hub History</h2>
                    <p style={{ fontSize: '0.9rem', color: '#64748b', margin: 0 }}>Review active audits, trace changes, or restore deleted objects in {selectedOrg?.name}</p>
                  </div>
                </div>
                {/* Premium Sub-Tab Pills */}
                <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem', borderBottom: '1px solid #e2e8f0', paddingBottom: '0.75rem' }}>
                  <button
                    onClick={() => setHistorySubTab('logs')}
                    style={{
                      padding: '0.5rem 1.25rem',
                      borderRadius: '20px',
                      border: 'none',
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      background: historySubTab === 'logs' ? '#6366f1' : '#f1f5f9',
                      color: historySubTab === 'logs' ? 'white' : '#64748b',
                      boxShadow: historySubTab === 'logs' ? '0 4px 6px -1px rgba(99, 102, 241, 0.2)' : 'none'
                    }}
                  >
                    Activity Logs ({logs.length})
                  </button>
                  <button
                    onClick={() => setHistorySubTab('recovery')}
                    style={{
                      padding: '0.5rem 1.25rem',
                      borderRadius: '20px',
                      border: 'none',
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      background: historySubTab === 'recovery' ? '#ef4444' : '#f1f5f9',
                      color: historySubTab === 'recovery' ? 'white' : '#64748b',
                      boxShadow: historySubTab === 'recovery' ? '0 4px 6px -1px rgba(239, 68, 68, 0.2)' : 'none'
                    }}
                  >
                    Recovery Section ({recoveryItems.length})
                  </button>
                </div>
                {error && <div className="error-message" style={{ marginBottom: '1.5rem' }}>{error}</div>}
                {message && <div className="success-message" style={{ marginBottom: '1.5rem' }}>{message}</div>}
                <div className="requests-container">
                  {historySubTab === 'logs' && (
                    logs.length === 0 ? (
                      <div className="empty-requests">
                        <History size={36} color="#cbd5e1" />
                        <p>No activity recorded yet.</p>
                      </div>
                    ) : (
                      <div className="request-list" style={{ maxHeight: 'calc(100vh - 320px)', overflowY: 'auto' }}>
                        {logs.map((item, idx) => (
                          <div
                            key={idx}
                            className="request-item"
                            onClick={() => setSelectedHistoryLog(item)}
                            style={{ padding: '1.1rem 1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', transition: 'background 0.2s' }}
                            onMouseEnter={e => e.currentTarget.style.background = '#f8fafc'}
                            onMouseLeave={e => e.currentTarget.style.background = 'white'}
                          >
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
                                <span style={{ fontWeight: 600, color: '#0f172a', fontSize: '0.9rem' }}>{item.email}</span>
                                {item.role && <span className="role-chip" style={{ fontSize: '0.72rem', textTransform: 'capitalize' }}>{item.role}</span>}
                                <span style={{
                                  fontSize: '0.72rem', fontWeight: 600, padding: '0.15rem 0.5rem', borderRadius: '6px',
                                  background: (item.status === 'accepted' || item.status === 'approved') ? '#ecfdf5' : item.status === 'pending' ? '#fff7ed' : '#fef2f2',
                                  color: (item.status === 'accepted' || item.status === 'approved') ? '#059669' : item.status === 'pending' ? '#c2410c' : '#ef4444',
                                  textTransform: 'capitalize'
                                }}>{item.status}</span>
                                <span style={{ fontSize: '0.68rem', fontWeight: 600, padding: '0.12rem 0.45rem', borderRadius: '4px', background: item.type === 'invitation' ? '#eef2ff' : '#f0fdf4', color: item.type === 'invitation' ? '#6366f1' : '#16a34a', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                                  {item.type === 'invitation' ? '✉ Invite' : '🙋 Join Req'}
                                </span>
                              </div>
                              <div style={{ fontSize: '0.82rem', color: '#64748b' }}>
                                {item.type === 'invitation'
                                  ? <span>Invited by <strong style={{ color: '#475569' }}>{item.invited_by}</strong></span>
                                  : <span>Requested to join workspace</span>
                                }
                                {item.message && <span style={{ fontStyle: 'italic', marginLeft: '0.4rem' }}>— "{item.message}"</span>}
                              </div>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexShrink: 0, marginLeft: '1rem' }}>
                              <div style={{ fontSize: '0.8rem', color: '#94a3b8', fontWeight: 500, whiteSpace: 'nowrap' }}>
                                {new Date(item.timestamp).toLocaleDateString()} · {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })}
                              </div>
                              {item.type === 'join_request' && item.status === 'pending' && (
                                <div style={{ display: 'flex', gap: '0.5rem' }}>
                                  <button disabled={loading}
                                    onClick={async (e) => {
                                      e.stopPropagation();
                                      setLoading(true);
                                      try {
                                        await manageJoinRequest(selectedOrg.id, item.id, 'approve');
                                        setMessage(`✅ ${item.email}'s request approved. Email sent.`);
                                        const [history, reqs] = await Promise.all([
                                          getWorkspaceHistory(selectedOrg.id).catch(() => []),
                                          getJoinRequests(selectedOrg.id).catch(() => [])
                                        ]);
                                        setWorkspaceHistory(history);
                                        setJoinRequests(reqs);
                                      } catch (err) { setError('Failed to approve request.'); }
                                      finally { setLoading(false); }
                                    }}
                                    style={{ padding: '0.35rem 0.8rem', background: '#22c55e', color: 'white', border: 'none', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer', transition: 'all 0.15s' }}
                                    onMouseOver={e => e.currentTarget.style.background = '#16a34a'}
                                    onMouseOut={e => e.currentTarget.style.background = '#22c55e'}
                                  >✓ Approve</button>
                                  <button disabled={loading}
                                    onClick={async (e) => {
                                      e.stopPropagation();
                                      setLoading(true);
                                      try {
                                        await manageJoinRequest(selectedOrg.id, item.id, 'deny');
                                        setMessage(`❌ ${item.email}'s request denied. Email sent.`);
                                        const [history, reqs] = await Promise.all([
                                          getWorkspaceHistory(selectedOrg.id).catch(() => []),
                                          getJoinRequests(selectedOrg.id).catch(() => [])
                                        ]);
                                        setWorkspaceHistory(history);
                                        setJoinRequests(reqs);
                                      } catch (err) { setError('Failed to deny request.'); }
                                      finally { setLoading(false); }
                                    }}
                                    style={{ padding: '0.35rem 0.8rem', background: '#ef4444', color: 'white', border: 'none', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer', transition: 'all 0.15s' }}
                                    onMouseOver={e => e.currentTarget.style.background = '#dc2626'}
                                    onMouseOut={e => e.currentTarget.style.background = '#ef4444'}
                                  >✕ Deny</button>
                                </div>
                              )}
                              {item.type === 'invitation' && item.status === 'pending' && item.email.toLowerCase() === sessionStorage.getItem('email')?.toLowerCase() && (
                                <div style={{ display: 'flex', gap: '0.5rem' }}>
                                  <button disabled={loading}
                                    onClick={async (e) => {
                                      e.stopPropagation();
                                      setLoading(true);
                                      try {
                                        await acceptInvitation(item.id);
                                        setMessage(`✅ Invitation accepted for ${item.email}. Email sent.`);
                                        const history = await getWorkspaceHistory(selectedOrg.id).catch(() => []);
                                        setWorkspaceHistory(history);
                                      } catch (err) { setError(err.response?.data?.error || 'Failed to accept invitation.'); }
                                      finally { setLoading(false); }
                                    }}
                                    style={{ padding: '0.35rem 0.8rem', background: '#6366f1', color: 'white', border: 'none', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer', transition: 'all 0.15s' }}
                                    onMouseOver={e => e.currentTarget.style.background = '#4f46e5'}
                                    onMouseOut={e => e.currentTarget.style.background = '#6366f1'}
                                  >✓ Accept</button>
                                  <button disabled={loading}
                                    onClick={async (e) => {
                                      e.stopPropagation();
                                      setLoading(true);
                                      try {
                                        await declineInvitation(item.id);
                                        setMessage(`Invitation declined for ${item.email}. Email sent.`);
                                        const history = await getWorkspaceHistory(selectedOrg.id).catch(() => []);
                                        setWorkspaceHistory(history);
                                      } catch (err) { setError(err.response?.data?.error || 'Failed to decline invitation.'); }
                                      finally { setLoading(false); }
                                    }}
                                    style={{ padding: '0.35rem 0.8rem', background: '#94a3b8', color: 'white', border: 'none', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer', transition: 'all 0.15s' }}
                                    onMouseOver={e => e.currentTarget.style.background = '#64748b'}
                                    onMouseOut={e => e.currentTarget.style.background = '#94a3b8'}
                                  >✕ Decline</button>
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )
                  )}
                  {historySubTab === 'recovery' && (
                    /* Recovery / Trash Section */
                    recoveryItems.length === 0 ? (
                      <div className="empty-requests" style={{ padding: '3rem 1rem' }}>
                        <Trash2 size={40} style={{ color: '#94a3b8', marginBottom: '0.75rem' }} />
                        <p style={{ fontWeight: 600, color: '#64748b' }}>Recovery Vault is Empty</p>
                        <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.25rem' }}>No recently removed members, deleted notes, or deleted goals found.</p>
                      </div>
                    ) : (
                      <div className="request-list" style={{ maxHeight: 'calc(100vh - 320px)', overflowY: 'auto' }}>
                        {recoveryItems.map((item, idx) => (
                          <div
                            key={idx}
                            className="request-item"
                            onClick={() => setSelectedHistoryLog(item)}
                            style={{ padding: '1.1rem 1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderLeft: '3px solid #ef4444', cursor: 'pointer', transition: 'background 0.2s' }}
                            onMouseEnter={e => e.currentTarget.style.background = '#fef2f2'}
                            onMouseLeave={e => e.currentTarget.style.background = 'white'}
                          >
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                                <span style={{ fontWeight: 600, color: '#0f172a', fontSize: '0.9rem' }}>
                                  {item.type === 'removed_member' ? item.email : item.title || 'Untitled'}
                                </span>
                                <span style={{
                                  fontSize: '0.7rem',
                                  fontWeight: 700,
                                  padding: '0.15rem 0.5rem',
                                  borderRadius: '4px',
                                  background: item.type === 'removed_member' ? '#fee2e2' : item.type === 'deleted_note' ? '#fef3c7' : '#e0f2fe',
                                  color: item.type === 'removed_member' ? '#ef4444' : item.type === 'deleted_note' ? '#d97706' : '#0369a1',
                                  textTransform: 'uppercase'
                                }}>
                                  {item.type === 'removed_member' ? 'Removed Member' : item.type === 'deleted_note' ? 'Deleted Note' : 'Deleted Goal'}
                                </span>
                              </div>
                              <div style={{ fontSize: '0.82rem', color: '#64748b' }}>
                                {item.type === 'removed_member' ? (
                                  <span>Previously matched role: <strong style={{ color: '#475569', textTransform: 'capitalize' }}>{item.role}</strong></span>
                                ) : item.type === 'deleted_note' ? (
                                  <span>Notebook note created by <strong style={{ color: '#475569' }}>{item.email}</strong></span>
                                ) : (
                                  <span>OKR goal created by <strong style={{ color: '#475569' }}>{item.email}</strong></span>
                                )}
                              </div>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                              <div style={{ fontSize: '0.8rem', color: '#94a3b8', fontWeight: 500, textAlign: 'right', whiteSpace: 'nowrap' }}>
                                {new Date(item.timestamp).toLocaleDateString()}
                              </div>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  if (item.type === 'removed_member') {
                                    handleRestoreMember(item.id);
                                  } else if (item.type === 'deleted_note') {
                                    handleRestoreNote(item.id);
                                  } else {
                                    handleRestoreGoal(item.id);
                                  }
                                }}
                                disabled={loading}
                                style={{
                                  padding: '0.4rem 0.9rem',
                                  backgroundColor: '#22c55e',
                                  color: 'white',
                                  border: 'none',
                                  borderRadius: '6px',
                                  fontSize: '0.78rem',
                                  fontWeight: 600,
                                  cursor: 'pointer',
                                  transition: 'all 0.15s',
                                  boxShadow: '0 2px 4px rgba(34, 197, 94, 0.2)'
                                }}
                                onMouseOver={e => e.currentTarget.style.backgroundColor = '#16a34a'}
                                onMouseOut={e => e.currentTarget.style.backgroundColor = '#22c55e'}
                              >
                                {loading ? 'Restoring...' : 'Restore'}
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )
                  )}
                </div>
              </div>
            );
          })()}
          {activeTab === 'calendar' && (
            <div style={{ maxWidth: '1200px', margin: '0 auto', height: '100%', display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                <div>
                  <h2 className="section-title-premium" style={{ marginBottom: '0.25rem' }}>Workspace Calendar</h2>
                  <p style={{ fontSize: '0.9rem', color: '#64748b', margin: 0 }}>{selectedOrg?.name} • Drag & Drop to Reschedule</p>
                </div>
              </div>
              <div style={{ flex: 1, minHeight: '600px' }}>
                <WorkspaceCalendar
                  selectedOrg={selectedOrg}
                  handleTaskClick={(id) => { setActiveTab('tasks'); handleTaskClick({ id }); }}
                  handleGoalClick={async (id) => {
                    try {
                      const detail = await getGoalDetail(id);
                      setActiveGoal(detail);
                      setGoalsView('detail');
                      setActiveTab('goals');
                    } catch (e) { console.error(e); }
                  }}
                />
              </div>
            </div>
          )}
          {activeTab === 'goals' && (() => {
            const canCreateGoals = () => {
              const role = selectedOrg?.my_status?.role;
              if (role === 'owner' || role === 'admin') return true;
              const customPerms = selectedOrg?.my_status?.custom_permissions || {};
              return customPerms.create_workspace_goals !== undefined ? !!customPerms.create_workspace_goals : true;
            };
            const canEditGoal = (goal) => {
              const role = selectedOrg?.my_status?.role;
              if (role === 'owner' || role === 'admin') return true;
              const customPerms = selectedOrg?.my_status?.custom_permissions || {};
              const hasGranularEdit = customPerms.edit_goals !== undefined ? !!customPerms.edit_goals : false;
              if (!hasGranularEdit) return false;
              const currentUserEmail = sessionStorage.getItem('email');
              const isCreator = goal?.created_by_details?.email === currentUserEmail;
              const isOwner = goal?.owner_details?.email === currentUserEmail;
              const isAssignee = goal?.assignees?.some(a => a.email === currentUserEmail);
              return isCreator || isOwner || isAssignee;
            };
            const canDeleteGoal = () => {
              const role = selectedOrg?.my_status?.role;
              if (role === 'owner' || role === 'admin') return true;
              const customPerms = selectedOrg?.my_status?.custom_permissions || {};
              return customPerms.delete_workspace_goals !== undefined ? !!customPerms.delete_workspace_goals : false;
            };
            // Filters & Search
            const activeUserEmail = sessionStorage.getItem('email')?.toLowerCase();
            const filteredGoals = goals.filter(g => {
              const matchesSearch = g.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                (g.owner_email && g.owner_email.toLowerCase().includes(searchQuery.toLowerCase()));
              return matchesSearch;
            });
            return (
              <div className="goals-tab-container" style={{ maxWidth: '1100px', margin: '0 auto', padding: '1rem' }}>
                {goalsView === 'list' && (
                  <>
                    {/* Top Action Header */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                      <div>
                        <h2 className="section-title-premium" style={{ marginBottom: '0.25rem' }}>Goals Hub</h2>
                        <p className="section-subtitle-premium" style={{ marginBottom: 0 }}>
                          Track goals, align your team, and measure key results in real time.
                        </p>
                      </div>
                      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                        <button
                          className={canCreateGoals() ? "btn-primary" : "btn-primary disabled"}
                          onClick={() => {
                            if (!canCreateGoals()) return;
                            setGoalsView('create');
                            const currentMember = orgMembers.find(m => m.email.toLowerCase() === sessionStorage.getItem('email')?.toLowerCase());
                            setNewGoalData({
                              title: '',
                              description: '',
                              owner: currentMember ? currentMember.user_id : '', // Default to self user_id
                              priority: 'medium',
                              visibility_type: 'specific',
                              visible_to: [],
                              parent: '',
                              depends_on: '',
                              timeframe: 'quarterly',
                              template_type: 'none',
                              is_shared_externally: false
                            });
                          }}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            width: 'auto',
                            height: '40px',
                            padding: '0.65rem 1.3rem',
                            fontSize: '0.85rem',
                            fontWeight: 600,
                            borderRadius: '8px',
                            opacity: canCreateGoals() ? 1 : 0.5,
                            cursor: canCreateGoals() ? 'pointer' : 'not-allowed',
                            margin: 0,
                            whiteSpace: 'nowrap'
                          }}
                          disabled={!canCreateGoals()}
                          title={canCreateGoals() ? "Create new goal" : "You do not have permission to create goals."}
                        >
                          <Plus size={16} style={{ marginRight: '0.5rem' }} /> New Goal
                        </button>
                      </div>
                    </div>
                    {/* Search & Filter Bar */}
                    <div className="goals-search-bar" style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', position: 'relative' }}>
                      <div style={{ position: 'relative', flex: 1 }}>
                        <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
                        <input
                          type="text"
                          className="input-field"
                          placeholder="Search goals by title or owner..."
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          style={{ paddingLeft: '2.5rem', borderRadius: '8px', fontSize: '0.85rem' }}
                        />
                      </div>
                    </div>
                    {error && <div className="error-message" style={{ marginBottom: '1.5rem' }}>{error}</div>}
                    {message && <div className="success-message" style={{ marginBottom: '1.5rem' }}>{message}</div>}
                    {/* Goals List Grid */}
                    {filteredGoals.length === 0 ? (
                      <div className="premium-card-settings" style={{ padding: '3.5rem 2rem', textAlign: 'center', color: '#64748b' }}>
                        <Target size={48} style={{ margin: '0 auto 1rem', color: '#cbd5e1' }} />
                        <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#1e293b' }}>No Goals Defined Yet</h3>
                        <p style={{ fontSize: '0.875rem', marginTop: '0.5rem', color: '#64748b' }}>
                          Get started by creating your first goal. Set Key Results to track progress!
                        </p>
                        <button
                          className={canCreateGoals() ? "btn-primary" : "btn-primary disabled"}
                          onClick={() => {
                            if (!canCreateGoals()) return;
                            setGoalsView('create');
                          }}
                          style={{
                            width: 'auto',
                            margin: '1.25rem auto 0',
                            padding: '0.6rem 1.5rem',
                            opacity: canCreateGoals() ? 1 : 0.5,
                            cursor: canCreateGoals() ? 'pointer' : 'not-allowed'
                          }}
                          disabled={!canCreateGoals()}
                          title={canCreateGoals() ? "Create goal" : "You do not have permission to create goals."}
                        >
                          Create First Goal
                        </button>
                      </div>
                    ) : (
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.25rem' }}>
                        {filteredGoals.map(goal => {
                          const progressVal = parseFloat(goal.computed_progress ?? goal.progress ?? 0);
                          let statusText = 'Not Started';
                          let statusClass = 'not-started';
                          if (goal.status === 'in_progress') { statusText = 'In Progress'; statusClass = 'in-progress'; }
                          if (goal.status === 'at_risk') { statusText = 'At Risk'; statusClass = 'at-risk'; }
                          if (goal.status === 'completed') { statusText = 'Completed'; statusClass = 'completed'; }
                          return (
                            <div
                              key={goal.id}
                              className="member-row-premium hover-premium-goal-card"
                              style={{ display: 'flex', flexDirection: 'column', alignItems: 'stretch', gap: '1rem', padding: '1.25rem', cursor: 'pointer', borderRadius: '12px', border: '1px solid #e2e8f0', background: 'white' }}
                              onClick={async () => {
                                setLoading(true);
                                try {
                                  const detail = await getGoalDetail(goal.id);
                                  setActiveGoal(detail);
                                  setGoalsView('detail');
                                } catch (e) {
                                  console.error(e);
                                } finally {
                                  setLoading(false);
                                }
                              }}
                            >
                              {/* Card Header */}
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                <div style={{ flex: 1, textAlign: 'left' }}>
                                  <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a', margin: 0, lineHeight: 1.3 }}>{goal.title}</h3>
                                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.25rem', alignItems: 'center' }}>
                                    <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
                                      Owner: {goal.owner_email || 'Unassigned'}
                                    </span>
                                    {goal.timeframe && (
                                      <span style={{ fontSize: '0.68rem', background: '#f1f5f9', color: '#475569', padding: '0.1rem 0.35rem', borderRadius: '4px', textTransform: 'capitalize', fontWeight: 600 }}>
                                        {goal.timeframe}
                                      </span>
                                    )}
                                    {goal.template_type && goal.template_type !== 'none' && (
                                      <span style={{ fontSize: '0.68rem', background: '#eef2ff', color: '#4f46e5', padding: '0.1rem 0.35rem', borderRadius: '4px', textTransform: 'capitalize', fontWeight: 600 }}>
                                        Template
                                      </span>
                                    )}
                                    {goal.is_shared_externally && (
                                      <span style={{ fontSize: '0.68rem', background: '#ecfdf5', color: '#059669', padding: '0.1rem 0.35rem', borderRadius: '4px', fontWeight: 600 }}>
                                        🔓 External
                                      </span>
                                    )}
                                  </div>
                                </div>
                                <span className={`member-role-badge-premium role-${goal.priority}`} style={{ textTransform: 'capitalize', fontSize: '0.7rem', padding: '0.2rem 0.5rem' }}>
                                  {goal.priority}
                                </span>
                              </div>
                              {/* Progress Bar */}
                              <div style={{ marginTop: '0.25rem' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.35rem' }}>
                                  <span>Progress ({goal.kr_count > 0 ? `${goal.kr_count} Key Results` : goal.task_count > 0 ? `${goal.done_task_count || 0}/${goal.task_count} Tasks` : 'No tasks yet'})</span>
                                  <span>{progressVal}%</span>
                                </div>
                                <div style={{ width: '100%', height: '6px', background: '#f1f5f9', borderRadius: '4px', overflow: 'hidden' }}>
                                  <div
                                    style={{ width: `${progressVal}%`, height: '100%', background: progressVal >= 100 ? '#22c55e' : '#6366f1', borderRadius: '4px', transition: 'width 0.3s ease' }}
                                  />
                                </div>
                              </div>
                              {/* Card Footer */}
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid #f1f5f9', paddingTop: '0.75rem', marginTop: '0.25rem' }}>
                                <span className={`member-role-badge-premium status-${statusClass}`} style={{ fontSize: '0.75rem' }}>
                                  {statusText}
                                </span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </>
                )}
                {/* Create Goal Form */}
                {goalsView === 'create' && (
                  <div style={{ maxWidth: '640px', margin: '0 auto' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
                      <button
                        className="note-save-btn"
                        onClick={() => setGoalsView('list')}
                        style={{ padding: '0.4rem 0.8rem', background: '#f8fafc' }}
                      >
                        &larr; Back to hub
                      </button>
                      <h2 className="section-title-premium" style={{ fontSize: '1.25rem', margin: 0 }}>Create Workspace Goal</h2>
                    </div>
                    <div className="premium-card-settings" style={{ background: 'white' }}>
                      <form onSubmit={handleCreateGoal}>
                        <div className="input-group">
                          <label className="input-label">Goal Title *</label>
                          <input
                            type="text"
                            className="input-field"
                            placeholder="e.g. Launch the New Q3 Marketing Campaign"
                            value={newGoalData.title}
                            onChange={(e) => setNewGoalData({ ...newGoalData, title: e.target.value })}
                            required
                          />
                        </div>
                        <div className="input-group">
                          <label className="input-label">Description / Alignment Info</label>
                          <textarea
                            className="input-field"
                            placeholder="Describe the context of this goal, its strategic alignment, or what success looks like..."
                            value={newGoalData.description}
                            onChange={(e) => setNewGoalData({ ...newGoalData, description: e.target.value })}
                            rows={3}
                          />
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                          <div className="input-group">
                            <label className="input-label">Goal Owner</label>
                            <select
                              className="input-field"
                              value={newGoalData.owner}
                              onChange={(e) => setNewGoalData({ ...newGoalData, owner: e.target.value })}
                              style={{ background: 'white' }}
                            >
                              <option value="">Select Owner</option>
                              {orgMembers.map(m => (
                                <option key={m.id} value={m.user_id}>{m.email}{m.is_on_leave ? ' (On Leave)' : ''}</option>
                              ))}
                            </select>
                          </div>
                          <div className="input-group">
                            <label className="input-label">Priority</label>
                            <select
                              className="input-field"
                              value={newGoalData.priority}
                              onChange={(e) => setNewGoalData({ ...newGoalData, priority: e.target.value })}
                              style={{ background: 'white' }}
                            >
                              <option value="low">Low</option>
                              <option value="medium">Medium</option>
                              <option value="high">High</option>
                            </select>
                          </div>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                          <div className="input-group">
                            <label className="input-label">Parent Goal (Hierarchy)</label>
                            <select
                              className="input-field"
                              value={newGoalData.parent || ''}
                              onChange={(e) => setNewGoalData({ ...newGoalData, parent: e.target.value })}
                              style={{ background: 'white' }}
                            >
                              <option value="">None (Top-Level Goal)</option>
                              {goals.map(g => (
                                <option key={g.id} value={g.id}>{g.title}</option>
                              ))}
                            </select>
                          </div>
                          <div className="input-group">
                            <label className="input-label">Depends On (Dependency)</label>
                            <select
                              className="input-field"
                              value={newGoalData.depends_on || ''}
                              onChange={(e) => setNewGoalData({ ...newGoalData, depends_on: e.target.value })}
                              style={{ background: 'white' }}
                            >
                              <option value="">None</option>
                              {goals.map(g => (
                                <option key={g.id} value={g.id}>{g.title}</option>
                              ))}
                            </select>
                          </div>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '0.5rem', marginBottom: '1.25rem' }}>
                          <div className="task-form-group">
                            <label className="task-form-label">Sharing & Permissions</label>
                            <button
                              type="button"
                              onClick={() => openSharingModal('newGoalData', newGoalData)}
                              style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem', background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '8px', cursor: 'pointer', color: '#334155', fontWeight: 500, justifyContent: 'space-between', width: '100%', outline: 'none' }}
                            >
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <Users size={16} style={{ color: '#6366f1' }} />
                                <span>
                                  {newGoalData.sharing_option === 'private' ? 'Private' : newGoalData.sharing_option === 'specific' ? 'Specific People' : 'Entire Workspace'}
                                </span>
                                <span style={{ fontSize: '0.75rem', color: '#94a3b8', marginLeft: '0.5rem' }}>
                                  ({newGoalData.assignees?.length || 0} Assignees
                                  {newGoalData.sharing_option === 'specific' ? `, ${newGoalData.shared_viewers?.length || 0} Viewers` : ''})
                                </span>
                              </div>
                            </button>
                          </div>
                          <div className="input-group" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.5rem' }}>
                            <input
                              type="checkbox"
                              id="is_shared_externally_checkbox"
                              checked={newGoalData.is_shared_externally}
                              onChange={(e) => setNewGoalData({ ...newGoalData, is_shared_externally: e.target.checked })}
                              style={{ width: 'auto', cursor: 'pointer', margin: 0 }}
                            />
                            <label htmlFor="is_shared_externally_checkbox" className="input-label" style={{ margin: 0, cursor: 'pointer', fontSize: '0.82rem', userSelect: 'none' }}>
                              Share Goal with external stakeholders
                            </label>
                          </div>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '2rem' }}>
                          <button
                            type="button"
                            className="note-save-btn"
                            onClick={() => setGoalsView('list')}
                            style={{ padding: '0.65rem 1.5rem' }}
                          >
                            Cancel
                          </button>
                          <button
                            type="submit"
                            className="btn-primary"
                            disabled={loading}
                            style={{ width: 'auto', padding: '0.65rem 2rem' }}
                          >
                            {loading ? 'Creating...' : 'Create Goal'}
                          </button>
                        </div>
                      </form>
                    </div>
                  </div>
                )}
                {/* Goal Detail View */}
                {goalsView === 'detail' && activeGoal && (
                  <div>
                    {/* Navigation & Action Header */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                      <button
                        className="note-save-btn"
                        onClick={() => setGoalsView('list')}
                        style={{ padding: '0.4rem 0.8rem', background: '#f8fafc' }}
                      >
                        &larr; Back to hub
                      </button>
                      <div style={{ display: 'flex', gap: '0.75rem' }}>
                        {canEditGoal(activeGoal) && (
                          <button
                            className="note-save-btn"
                            onClick={() => setGoalsView('edit')}
                            style={{ padding: '0.4rem 1rem' }}
                          >
                            Edit
                          </button>
                        )}
                        {canDeleteGoal() && (
                          <button
                            className="remove-btn-premium"
                            onClick={() => handleDeleteGoal(activeGoal.id)}
                            style={{ padding: '0.4rem 1rem', background: '#fee2e2', color: '#ef4444', border: '1px solid #fecaca' }}
                          >
                            Delete
                          </button>
                        )}
                      </div>
                    </div>
                    {/* Header line separated */}
                    <div style={{ borderBottom: '1px solid #e2e8f0', background: 'white' }}></div>
                    {/* Main Body */}
                    <div style={{ display: goalDetailTab === 'details' ? 'block' : 'none' }}>
                      {/* Read-Only Warning Banner */}
                      {!canEditGoal(activeGoal) && (
                        <div style={{
                          background: '#fffbeb',
                          border: '1px solid #fef3c7',
                          borderRadius: '12px',
                          padding: '1rem',
                          marginBottom: '1.25rem',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.75rem',
                          boxShadow: '0 1px 3px rgba(0,0,0,0.02)'
                        }}>
                          <div style={{ background: '#fef3c7', color: '#d97706', width: '32px', height: '32px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                            ⚠️
                          </div>
                          <div style={{ textAlign: 'left' }}>
                            <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#92400e', margin: 0 }}>Read-Only Mode</h4>
                            <p style={{ fontSize: '0.75rem', color: '#b45309', margin: '0.1rem 0 0 0' }}>
                              You do not have permission to edit this goal or its key results because of workspace granular permission rules.
                            </p>
                          </div>
                        </div>
                      )}
                      {/* Detail Grid */}
                      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem', alignItems: 'flex-start' }}>
                        {/* Left Column: Info & OKRs */}
                        <div className="premium-card-settings" style={{ background: 'white', textAlign: 'left', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                          <div>
                            <span className={`member-role-badge-premium role-${activeGoal.priority}`} style={{ textTransform: 'capitalize', fontSize: '0.7rem', marginBottom: '0.5rem', display: 'inline-block' }}>
                              {activeGoal.priority} Priority
                            </span>
                            <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>{activeGoal.title}</h2>
                            <p style={{ fontSize: '0.9rem', color: '#475569', marginTop: '0.75rem', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>
                              {activeGoal.description || 'No description provided.'}
                            </p>
                            <button
                              onClick={() => {
                                if (activeGoal.chat_room_id) {
                                  setInitialChatRoomId(activeGoal.chat_room_id);
                                  setActiveTab('chat');
                                  setActiveGoal(null);
                                } else {
                                  alert('Chat room not ready yet.');
                                }
                              }}
                              style={{
                                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
                                width: '100%', padding: '0.85rem', backgroundColor: '#6366f1', color: '#ffffff',
                                border: 'none', borderRadius: '8px', fontSize: '0.95rem', fontWeight: 600,
                                cursor: 'pointer', transition: 'background-color 0.2s', marginTop: '0.5rem'
                              }}
                              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#4f46e5'}
                              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#6366f1'}
                            >
                              <MessageSquare size={18} /> Chat
                            </button>
                          </div>
                          {/* Key Results / OKRs Tracking */}
                          <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '1.5rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
                              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#1e293b', margin: 0 }}>Key Results (OKRs Tracking)</h3>
                              {canEditGoal(activeGoal) && (
                                <button
                                  className="note-save-btn"
                                  onClick={() => {
                                    setShowAddKr(!showAddKr);
                                    setKrForm({ title: '', target_value: 100.0, current_value: 0.0, unit: '%' });
                                  }}
                                  style={{ fontSize: '0.75rem', padding: '0.3rem 0.75rem' }}
                                >
                                  {showAddKr ? 'Cancel' : '+ Add Key Result'}
                                </button>
                              )}
                            </div>
                            {/* Add Key Result form */}
                            {showAddKr && (
                              <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '1.25rem' }}>
                                <form onSubmit={handleCreateKr}>
                                  <div className="input-group">
                                    <label className="input-label" style={{ fontSize: '0.7rem' }}>Key Result Metric Title</label>
                                    <input
                                      type="text"
                                      className="input-field"
                                      placeholder="e.g. Close 15 premium contract accounts"
                                      value={krForm.title}
                                      onChange={(e) => setKrForm({ ...krForm, title: e.target.value })}
                                      required
                                      style={{ padding: '0.45rem', fontSize: '0.8rem' }}
                                    />
                                  </div>
                                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem' }}>
                                    <div className="input-group">
                                      <label className="input-label" style={{ fontSize: '0.7rem' }}>Current Value</label>
                                      <input
                                        type="number"
                                        className="input-field"
                                        value={krForm.current_value}
                                        onChange={(e) => setKrForm({ ...krForm, current_value: parseFloat(e.target.value) })}
                                        required
                                        style={{ padding: '0.45rem', fontSize: '0.8rem' }}
                                      />
                                    </div>
                                    <div className="input-group">
                                      <label className="input-label" style={{ fontSize: '0.7rem' }}>Target Value</label>
                                      <input
                                        type="number"
                                        className="input-field"
                                        value={krForm.target_value}
                                        onChange={(e) => setKrForm({ ...krForm, target_value: parseFloat(e.target.value) })}
                                        required
                                        style={{ padding: '0.45rem', fontSize: '0.8rem' }}
                                      />
                                    </div>
                                    <div className="input-group">
                                      <label className="input-label" style={{ fontSize: '0.7rem' }}>Unit</label>
                                      <input
                                        type="text"
                                        className="input-field"
                                        value={krForm.unit}
                                        onChange={(e) => setKrForm({ ...krForm, unit: e.target.value })}
                                        required
                                        style={{ padding: '0.45rem', fontSize: '0.8rem' }}
                                      />
                                    </div>
                                  </div>
                                  <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.75rem' }}>
                                    <button type="submit" disabled={loading} className="btn-primary" style={{ width: 'auto', padding: '0.4rem 1.25rem', fontSize: '0.75rem' }}>
                                      Save Key Result
                                    </button>
                                  </div>
                                </form>
                              </div>
                            )}
                            {/* KR List with Real-time Interactive Sliders */}
                            {!activeGoal.key_results || activeGoal.key_results.length === 0 ? (
                              <div style={{ padding: '2rem', textAlign: 'center', background: '#f8fafc', borderRadius: '8px', color: '#94a3b8', fontSize: '0.85rem' }}>
                                No Key Results mapped to this goal. Add key metrics to measure goal progress!
                              </div>
                            ) : (
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                                {activeGoal.key_results.map(kr => {
                                  const target = parseFloat(kr.target_value);
                                  const current = parseFloat(kr.current_value);
                                  const progress = parseFloat(kr.progress || 0);
                                  return (
                                    <div key={kr.id} style={{ background: '#f8fafc', padding: '1rem', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                                        <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#1e293b' }}>{kr.title}</span>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                          <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>
                                            {current} / {target} {kr.unit} ({progress}%)
                                          </span>
                                          {canEditGoal(activeGoal) && (
                                            <button
                                              className="note-delete-btn"
                                              onClick={() => handleDeleteKr(kr.id)}
                                              style={{ padding: '4px' }}
                                            >
                                              <Trash2 size={12} />
                                            </button>
                                          )}
                                        </div>
                                      </div>
                                      {/* Real-time Interactive Slider */}
                                      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                        <input
                                          type="range"
                                          min="0"
                                          max={target}
                                          step={target / 100 || 1}
                                          value={current}
                                          disabled={!canEditGoal(activeGoal)}
                                          onChange={(e) => handleUpdateKrValue(kr.id, e.target.value)}
                                          style={{ flex: 1, accentColor: '#6366f1', cursor: canEditGoal(activeGoal) ? 'pointer' : 'not-allowed', height: '5px' }}
                                        />
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            )}
                          </div>
                          {/* Goal Tasks Section */}
                          <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '1.5rem', marginTop: '1.5rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
                              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#1e293b', margin: 0 }}>Linked Tasks</h3>
                              {canEditGoal(activeGoal) && (
                                <button
                                  className="note-save-btn"
                                  onClick={() => {
                                    setShowAddGoalTask(!showAddGoalTask);
                                    setGoalTaskForm({ title: '', estimated_hours: '', estimated_minutes: '', assignees: [] });
                                  }}
                                  style={{ fontSize: '0.75rem', padding: '0.3rem 0.75rem' }}
                                >
                                  {showAddGoalTask ? 'Cancel' : '+ Add Task'}
                                </button>
                              )}
                            </div>
                            {/* Add Task Form */}
                            {mustChangePassword && (
                              <div className="modal-overlay" style={{ zIndex: 9999 }}>
                                <div className="modal-card">
                                  <div className="logo-container" style={{ textAlign: 'center', marginBottom: '1rem' }}>
                                    <Lock size={32} color="#6366f1" />
                                  </div>
                                  <h2 className="form-title" style={{ textAlign: 'center' }}>Change Your Password</h2>
                                  <p className="form-subtitle" style={{ textAlign: 'center', marginBottom: '2rem' }}>For your security, please create a new password before continuing.</p>
                                  {error && <div className="error-message">{error}</div>}
                                  {message && <div className="success-message">{message}</div>}
                                  <form onSubmit={async (e) => {
                                    e.preventDefault();
                                    setLoading(true);
                                    setError('');
                                    try {
                                      if (changePasswordData.new_password !== changePasswordData.confirm_password) {
                                        setError("Passwords do not match");
                                        setLoading(false);
                                        return;
                                      }
                                      const email = sessionStorage.getItem('email');
                                      if (!email) throw new Error("Email not found in session");
                                      await changePassword(email, changePasswordData.new_password);
                                      setMessage('Password updated successfully!');
                                      sessionStorage.removeItem('mustChangePassword');
                                      setMustChangePassword(false);
                                      // Optionally reload workspaces or keep the user where they are
                                      await fetchWorkspaces(sessionStorage.getItem('access_token'));
                                    } catch (err) {
                                      setError(err.response?.data?.error || err.response?.data?.detail || 'Failed to update password');
                                    } finally {
                                      setLoading(false);
                                    }
                                  }}>
                                    <div className="input-group">
                                      <label>New Password</label>
                                      <div className="input-wrapper">
                                        <input
                                          type={showPassword ? "text" : "password"}
                                          value={changePasswordData.new_password}
                                          onChange={e => setChangePasswordData({ ...changePasswordData, new_password: e.target.value })}
                                          placeholder="Enter new password"
                                          required
                                        />
                                        <button type="button" className="password-toggle" onClick={() => setShowPassword(!showPassword)}>
                                          {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                                        </button>
                                      </div>
                                    </div>
                                    <div className="input-group">
                                      <label>Confirm Password</label>
                                      <div className="input-wrapper">
                                        <input
                                          type={showPassword ? "text" : "password"}
                                          value={changePasswordData.confirm_password}
                                          onChange={e => setChangePasswordData({ ...changePasswordData, confirm_password: e.target.value })}
                                          placeholder="Confirm new password"
                                          required
                                        />
                                      </div>
                                    </div>
                                    <button type="submit" className="submit-btn" disabled={loading}>
                                      {loading ? 'Updating...' : 'Update Password'}
                                    </button>
                                  </form>
                                </div>
                              </div>
                            )}
                            {showAddGoalTask && (
                              <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '1.25rem' }}>
                                <form onSubmit={handleCreateGoalTask}>
                                  <div className="input-group">
                                    <label className="input-label" style={{ fontSize: '0.7rem' }}>Task Title</label>
                                    <input
                                      type="text"
                                      className="input-field"
                                      placeholder="e.g. Design new landing page"
                                      value={goalTaskForm.title}
                                      onChange={(e) => setGoalTaskForm({ ...goalTaskForm, title: e.target.value })}
                                      required
                                      style={{ padding: '0.45rem', fontSize: '0.8rem' }}
                                    />
                                  </div>
                                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                                    <div className="input-group">
                                      <label className="input-label" style={{ fontSize: '0.7rem' }}>Est. Hours</label>
                                      <input
                                        type="number"
                                        min="0"
                                        placeholder="e.g. 2"
                                        className="input-field"
                                        value={goalTaskForm.estimated_hours}
                                        onChange={(e) => setGoalTaskForm({ ...goalTaskForm, estimated_hours: e.target.value })}
                                        style={{ padding: '0.45rem', fontSize: '0.8rem' }}
                                      />
                                    </div>
                                    <div className="input-group">
                                      <label className="input-label" style={{ fontSize: '0.7rem' }}>Est. Minutes</label>
                                      <input
                                        type="number"
                                        min="0"
                                        max="59"
                                        placeholder="e.g. 30"
                                        className="input-field"
                                        value={goalTaskForm.estimated_minutes}
                                        onChange={(e) => setGoalTaskForm({ ...goalTaskForm, estimated_minutes: e.target.value })}
                                        style={{ padding: '0.45rem', fontSize: '0.8rem' }}
                                      />
                                    </div>
                                  </div>
                                  <div className="input-group" style={{ marginTop: '0.5rem' }}>
                                    <label className="input-label" style={{ fontSize: '0.7rem' }}>Assignees</label>
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                                      {orgMembers.map(member => {
                                        const userId = member.user?.id || member.user_id;
                                        const isAssigned = goalTaskForm.assignees.includes(userId);
                                        return (
                                          <div
                                            key={userId}
                                            onClick={() => {
                                              let next = [...goalTaskForm.assignees];
                                              if (isAssigned) {
                                                next = next.filter(id => id !== userId);
                                              } else {
                                                if (next.length >= 1) {
                                                  alert("Warning: You cannot assign multiple members. A task can only have one unique member.");
                                                  return;
                                                }
                                                next.push(userId);
                                              }
                                              setGoalTaskForm({ ...goalTaskForm, assignees: next });
                                            }}
                                            style={{
                                              padding: '0.3rem 0.6rem',
                                              borderRadius: '999px',
                                              border: isAssigned ? '1px solid #6366f1' : '1px solid #cbd5e1',
                                              background: isAssigned ? '#eef2ff' : 'white',
                                              color: isAssigned ? '#6366f1' : '#475569',
                                              fontSize: '0.7rem',
                                              cursor: 'pointer',
                                              display: 'flex', alignItems: 'center', gap: '0.3rem'
                                            }}
                                          >
                                            <span>{member.email}{member.is_on_leave ? ' (On Leave)' : ''}</span>
                                          </div>
                                        );
                                      })}
                                    </div>
                                  </div>
                                  <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.75rem' }}>
                                    <button type="submit" disabled={loading} className="btn-primary" style={{ width: 'auto', padding: '0.4rem 1.25rem', fontSize: '0.75rem' }}>
                                      Create Task
                                    </button>
                                  </div>
                                </form>
                              </div>
                            )}
                            {/* Linked Tasks List */}
                            {tasks.filter(t => t.goal === activeGoal.id).length === 0 ? (
                              <div style={{ padding: '2rem', textAlign: 'center', background: '#f8fafc', borderRadius: '8px', color: '#94a3b8', fontSize: '0.85rem' }}>
                                No tasks linked to this goal yet.
                              </div>
                            ) : (
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                {tasks.filter(t => t.goal === activeGoal.id).map(task => (
                                  <div
                                    key={task.id}
                                    onClick={() => {
                                      setActiveTab('tasks');
                                      handleTaskClick(task);
                                    }}
                                    style={{
                                      display: 'flex',
                                      justifyContent: 'space-between',
                                      alignItems: 'center',
                                      padding: '0.75rem 1rem',
                                      background: 'white',
                                      borderRadius: '8px',
                                      border: '1px solid #e2e8f0',
                                      cursor: 'pointer',
                                      transition: 'all 0.2s ease'
                                    }}
                                    onMouseEnter={(e) => {
                                      e.currentTarget.style.borderColor = '#6366f1';
                                      e.currentTarget.style.background = '#f8fafc';
                                      e.currentTarget.style.transform = 'translateY(-1px)';
                                      e.currentTarget.style.boxShadow = '0 4px 6px -1px rgba(99, 102, 241, 0.05), 0 2px 4px -1px rgba(99, 102, 241, 0.03)';
                                    }}
                                    onMouseLeave={(e) => {
                                      e.currentTarget.style.borderColor = '#e2e8f0';
                                      e.currentTarget.style.background = 'white';
                                      e.currentTarget.style.transform = 'none';
                                      e.currentTarget.style.boxShadow = 'none';
                                    }}
                                  >
                                    <div>
                                      <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#0f172a' }}>{task.title}</div>
                                      <div style={{ fontSize: '0.75rem', color: '#64748b', display: 'flex', gap: '0.5rem', marginTop: '0.25rem' }}>
                                        <span style={{ textTransform: 'uppercase' }}>{task.status.replace('_', ' ')}</span>
                                        {task.due_date && <span>• Due: {new Date(task.due_date).toLocaleDateString()}</span>}
                                      </div>
                                    </div>
                                    <div style={{ display: 'flex', gap: '0.35rem' }}>
                                      {task.assignee_details?.map(u => (
                                        <div key={u.id} style={{ width: '20px', height: '20px', borderRadius: '50%', background: '#6366f1', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.6rem', fontWeight: 'bold' }} title={u.email}>
                                          {u.first_name?.[0] || u.email[0].toUpperCase()}
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                        {/* Right Column: Metadata details & Progress Radial */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                          <div className="premium-card-settings" style={{ background: 'white', textAlign: 'left' }}>
                            <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '1rem', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.5rem' }}>Goal Details</h3>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', fontSize: '0.85rem' }}>
                              <div>
                                <span style={{ color: '#94a3b8', display: 'block', fontSize: '0.75rem' }}>STATUS</span>
                                <span className={`member-role-badge-premium status-${activeGoal.status}`} style={{ display: 'inline-block', marginTop: '0.2rem' }}>
                                  {activeGoal.status === 'in_progress' ? 'In Progress' :
                                    activeGoal.status === 'at_risk' ? 'At Risk' :
                                      activeGoal.status === 'completed' ? 'Completed' : 'Not Started'}
                                </span>
                              </div>
                              <div>
                                <span style={{ color: '#94a3b8', display: 'block', fontSize: '0.75rem' }}>OWNER</span>
                                <span style={{ fontWeight: 600, color: '#1e293b' }}>
                                  {activeGoal.owner?.email || 'Unassigned'}
                                </span>
                              </div>
                              <div>
                                <span style={{ color: '#94a3b8', display: 'block', fontSize: '0.75rem' }}>START DATE</span>
                                <span style={{ fontWeight: 500, color: '#475569' }}>
                                  {activeGoal.start_date ? new Date(activeGoal.start_date).toLocaleDateString() : 'None'}
                                </span>
                              </div>
                              <div>
                                <span style={{ color: '#94a3b8', display: 'block', fontSize: '0.75rem' }}>TIMEFRAME</span>
                                <span style={{ fontWeight: 600, color: '#1e293b', textTransform: 'capitalize' }}>
                                  {activeGoal.timeframe || 'Quarterly'}
                                </span>
                              </div>
                              {activeGoal.parent_title && (
                                <div>
                                  <span style={{ color: '#94a3b8', display: 'block', fontSize: '0.75rem' }}>PARENT GOAL</span>
                                  <span style={{ fontWeight: 600, color: '#1e293b' }}>
                                    {activeGoal.parent_title}
                                  </span>
                                </div>
                              )}
                              {activeGoal.depends_on_title && (
                                <div>
                                  <span style={{ color: '#94a3b8', display: 'block', fontSize: '0.75rem' }}>BLOCKED BY (DEPENDENCY)</span>
                                  <span style={{ fontWeight: 600, color: '#ef4444' }}>
                                    {activeGoal.depends_on_title}
                                  </span>
                                </div>
                              )}
                              {activeGoal.template_type && activeGoal.template_type !== 'none' && (
                                <div>
                                  <span style={{ color: '#94a3b8', display: 'block', fontSize: '0.75rem' }}>GOAL TEMPLATE</span>
                                  <span style={{ fontWeight: 600, color: '#1e293b', textTransform: 'capitalize' }}>
                                    {activeGoal.template_type.replace('_', ' ')}
                                  </span>
                                </div>
                              )}
                              <div>
                                <span style={{ color: '#94a3b8', display: 'block', fontSize: '0.75rem' }}>VISIBILITY</span>
                                <span style={{ fontWeight: 500, color: '#475569', textTransform: 'capitalize' }}>
                                  {activeGoal.visibility_type} Scope
                                </span>
                              </div>
                              <div>
                                <span style={{ color: '#94a3b8', display: 'block', fontSize: '0.75rem' }}>EXTERNAL SHARING</span>
                                <span style={{ fontWeight: 600, color: activeGoal.is_shared_externally ? '#16a34a' : '#64748b' }}>
                                  {activeGoal.is_shared_externally ? '🔓 Enabled' : '🔒 Internal Only'}
                                </span>
                              </div>
                            </div>
                          </div>
                          {/* Progress Card */}
                          <div className="premium-card-settings" style={{ background: 'white', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '1.5rem' }}>
                            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '1rem' }}>Overall Progress</span>
                            <div style={{ position: 'relative', width: '100px', height: '100px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                              <svg style={{ transform: 'rotate(-90deg)', width: '100px', height: '100px' }}>
                                <circle
                                  cx="50" cy="50" r="40"
                                  stroke="#f1f5f9" strokeWidth="8" fill="transparent"
                                />
                                <circle
                                  cx="50" cy="50" r="40"
                                  stroke={parseFloat(activeGoal.progress) >= 100 ? '#22c55e' : '#6366f1'} strokeWidth="8" fill="transparent"
                                  strokeDasharray={2 * Math.PI * 40}
                                  strokeDashoffset={2 * Math.PI * 40 * (1 - parseFloat(activeGoal.progress || 0) / 100)}
                                  strokeLinecap="round"
                                  style={{ transition: 'stroke-dashoffset 0.3s ease' }}
                                />
                              </svg>
                              <span style={{ position: 'absolute', fontSize: '1.2rem', fontWeight: 800, color: '#0f172a' }}>
                                {parseInt(activeGoal.progress || 0)}%
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                {/* Edit Goal View */}
                {goalsView === 'edit' && activeGoal && (
                  <div style={{ maxWidth: '640px', margin: '0 auto' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
                      <button
                        className="note-save-btn"
                        onClick={() => setGoalsView('detail')}
                        style={{ padding: '0.4rem 0.8rem', background: '#f8fafc' }}
                      >
                        &larr; Back to detail
                      </button>
                      <h2 className="section-title-premium" style={{ fontSize: '1.25rem', margin: 0 }}>Edit Goal</h2>
                    </div>
                    <div className="premium-card-settings" style={{ background: 'white' }}>
                      <form onSubmit={handleUpdateGoal}>
                        <div className="input-group">
                          <label className="input-label">Goal Title *</label>
                          <input
                            type="text"
                            className="input-field"
                            value={activeGoal.title}
                            onChange={(e) => setActiveGoal({ ...activeGoal, title: e.target.value })}
                            required
                          />
                        </div>
                        <div className="input-group">
                          <label className="input-label">Description / Alignment Info</label>
                          <textarea
                            className="input-field"
                            value={activeGoal.description || ''}
                            onChange={(e) => setActiveGoal({ ...activeGoal, description: e.target.value })}
                            rows={3}
                          />
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                          <div className="input-group">
                            <label className="input-label">Goal Owner</label>
                            <select
                              className="input-field"
                              value={activeGoal.owner?.id || activeGoal.owner || ''}
                              onChange={(e) => setActiveGoal({ ...activeGoal, owner: e.target.value })}
                              style={{ background: 'white' }}
                            >
                              <option value="">Select Owner</option>
                              {orgMembers.map(m => (
                                <option key={m.id} value={m.user_id}>{m.email}{m.is_on_leave ? ' (On Leave)' : ''}</option>
                              ))}
                            </select>
                          </div>
                          <div className="input-group">
                            <label className="input-label">Priority</label>
                            <select
                              className="input-field"
                              value={activeGoal.priority}
                              onChange={(e) => setActiveGoal({ ...activeGoal, priority: e.target.value })}
                              style={{ background: 'white' }}
                            >
                              <option value="low">Low</option>
                              <option value="medium">Medium</option>
                              <option value="high">High</option>
                            </select>
                          </div>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                          <div className="input-group">
                            <label className="input-label">Parent Goal (Hierarchy)</label>
                            <select
                              className="input-field"
                              value={activeGoal.parent || ''}
                              onChange={(e) => setActiveGoal({ ...activeGoal, parent: e.target.value })}
                              style={{ background: 'white' }}
                            >
                              <option value="">None (Top-Level Goal)</option>
                              {goals.filter(g => g.id !== activeGoal.id).map(g => (
                                <option key={g.id} value={g.id}>{g.title}</option>
                              ))}
                            </select>
                          </div>
                          <div className="input-group">
                            <label className="input-label">Depends On (Dependency)</label>
                            <select
                              className="input-field"
                              value={activeGoal.depends_on || ''}
                              onChange={(e) => setActiveGoal({ ...activeGoal, depends_on: e.target.value })}
                              style={{ background: 'white' }}
                            >
                              <option value="">None</option>
                              {goals.filter(g => g.id !== activeGoal.id).map(g => (
                                <option key={g.id} value={g.id}>{g.title}</option>
                              ))}
                            </select>
                          </div>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '0.5rem', marginBottom: '1.25rem' }}>
                          <div className="input-group">
                            <label className="input-label">Sharing & Permissions</label>
                            <button
                              type="button"
                              onClick={() => openSharingModal('activeGoal', {
                                ...activeGoal,
                                assignees: (activeGoal.assignees || []).map(a => a.id || a.user_id || a),
                                shared_viewers: (activeGoal.shared_viewers || []).map(v => v.id || v.user_id || v)
                              })}
                              style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem', background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '8px', cursor: 'pointer', color: '#334155', fontWeight: 500, justifyContent: 'space-between', width: '100%', outline: 'none' }}
                            >
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <Users size={16} style={{ color: '#6366f1' }} />
                                <span>
                                  {activeGoal.sharing_option === 'private' ? 'Private' : activeGoal.sharing_option === 'specific' ? 'Specific People' : 'Entire Workspace'}
                                </span>
                                <span style={{ fontSize: '0.75rem', color: '#94a3b8', marginLeft: '0.5rem' }}>
                                  ({activeGoal.assignees?.length || 0} Assignees
                                  {activeGoal.sharing_option === 'specific' ? `, ${activeGoal.shared_viewers?.length || 0} Viewers` : ''})
                                </span>
                              </div>
                            </button>
                          </div>
                          <div className="input-group" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.5rem' }}>
                            <input
                              type="checkbox"
                              id="is_shared_externally_edit_checkbox"
                              checked={activeGoal.is_shared_externally || false}
                              onChange={(e) => setActiveGoal({ ...activeGoal, is_shared_externally: e.target.checked })}
                              style={{ width: 'auto', cursor: 'pointer', margin: 0 }}
                            />
                            <label htmlFor="is_shared_externally_edit_checkbox" className="input-label" style={{ margin: 0, cursor: 'pointer', fontSize: '0.82rem', userSelect: 'none' }}>
                              Share Goal with external stakeholders
                            </label>
                          </div>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '2rem' }}>
                          <button
                            type="button"
                            className="note-save-btn"
                            onClick={() => setGoalsView('detail')}
                            style={{ padding: '0.65rem 1.5rem' }}
                          >
                            Cancel
                          </button>
                          <button
                            type="submit"
                            className="btn-primary"
                            disabled={loading}
                            style={{ width: 'auto', padding: '0.65rem 2rem' }}
                          >
                            {loading ? 'Saving...' : 'Save Changes'}
                          </button>
                        </div>
                      </form>
                    </div>
                  </div>
                )}
              </div>
            );
          })()}
          {/* Tasks Tab */}
          {activeTab === 'tasks' && (() => {
            const canEditTask = (task) => {
              const role = selectedOrg?.my_status?.role;
              if (role === 'owner' || role === 'admin') return true;
              const customPerms = selectedOrg?.my_status?.custom_permissions || {};
              // 1. Explicit override block
              if (customPerms.edit_tasks === false) {
                return false;
              }
              // 2. Explicit workspace-wide permission override
              if (customPerms.edit_tasks === true) {
                return true;
              }
              // 3. Default member behavior: standard members cannot edit full task details (only status)
              return false;
            };
            const renderTaskDetailDrawer = () => {
              const isEditable = canEditTask(activeTask);
              const currentUserEmail = sessionStorage.getItem('email');
              const currentUserId = sessionStorage.getItem('userId');
              const isAssignee = (Array.isArray(activeTask?.assignees) && activeTask.assignees.some(a => {
                if (typeof a === 'object' && a !== null) {
                  return a.email === currentUserEmail || String(a.id) === String(currentUserId);
                }
                return String(a) === String(currentUserId);
              })) || (Array.isArray(activeTask?.assignee_details) && activeTask.assignee_details.some(d => d.email === currentUserEmail || String(d.id) === String(currentUserId)));
              const isCreator = activeTask?.created_by_details?.email === currentUserEmail || String(activeTask?.created_by) === String(currentUserId);
              const isStatusEditable = isEditable || isAssignee || isCreator;
              return (
                <div
                  className="task-detail-drawer"
                  style={{
                    width: '480px',
                    background: 'white',
                    borderLeft: '1px solid #e2e8f0',
                    boxShadow: '-10px 0 30px rgba(0, 0, 0, 0.08)',
                    position: 'fixed',
                    top: 0,
                    right: 0,
                    bottom: 0,
                    zIndex: 1000,
                    display: 'flex',
                    flexDirection: 'column',
                    animation: 'slideInTasksDrawer 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
                    height: '100vh',
                    textAlign: 'left'
                  }}
                >
                  <style>{`
                      @keyframes slideInTasksDrawer {
                        from { transform: translateX(100%); }
                        to { transform: translateX(0); }
                      }
                    `}</style>
                  {/* Drawer Header */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 1.25rem', borderBottom: '1px solid #f1f5f9', background: '#f8fafc' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span className="member-role-badge-premium role-medium" style={{ textTransform: 'uppercase', fontSize: '0.65rem' }}>{activeTask.issue_type}</span>
                      <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8' }}>Task Details</span>
                    </div>
                    <button
                      onClick={() => setTasksView('list')}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0.35rem', borderRadius: '50%', transition: 'background 0.2s' }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#e2e8f0'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                    >
                      <X size={18} />
                    </button>
                  </div>
                  {/* Header line separated */}
                  <div style={{ borderBottom: '1px solid #e2e8f0', background: 'white' }}></div>
                  {/* Main Body */}
                  <div style={{ overflowY: 'auto', flex: 1, padding: '1.25rem', flexDirection: 'column', gap: '1.25rem', display: 'flex' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                      {!isEditable && (
                        <div style={{ padding: '0.75rem 1rem', backgroundColor: (isAssignee || isCreator) ? '#eef2ff' : '#fffbeb', border: `1px solid ${(isAssignee || isCreator) ? '#e0e7ff' : '#fef3c7'}`, borderRadius: '12px', color: (isAssignee || isCreator) ? '#4f46e5' : '#b45309', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <AlertCircle size={16} />
                          <span>
                            {(isAssignee || isCreator)
                              ? "You can change status, but other details are read-only."
                              : 'You have read-only access. Grant "Edit & Update Tasks" permission to modify.'}
                          </span>
                        </div>
                      )}
                      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8' }}>
                        Created by {activeTask.created_by_details?.first_name || activeTask.created_by_details?.email}
                      </div>
                      <input
                        type="text"
                        value={activeTask.title || ''}
                        onChange={(e) => {
                          if (!isEditable) return;
                          setActiveTask({ ...activeTask, title: e.target.value });
                        }}
                        onBlur={async (e) => {
                          if (!isEditable) return;
                          if (!e.target.value.trim()) return;
                          try {
                            const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { title: e.target.value });
                            setActiveTask(updated);
                            handleLoadTasks();
                          } catch (err) {
                            console.error(err);
                          }
                        }}
                        readOnly={!isEditable}
                        style={{ cursor: isEditable ? 'pointer' : 'not-allowed', width: '100%', fontSize: '1.25rem', fontWeight: 800, border: 'none', borderBottom: '2px solid transparent', outline: 'none', padding: '0.2rem 0' }}
                        placeholder="Task Title"
                      />
                      <textarea
                        value={activeTask.description || ''}
                        onChange={(e) => {
                          if (!isEditable) return;
                          setActiveTask({ ...activeTask, description: e.target.value });
                        }}
                        onBlur={async (e) => {
                          if (!isEditable) return;
                          try {
                            const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { description: e.target.value });
                            setActiveTask(updated);
                            handleLoadTasks();
                          } catch (err) {
                            console.error(err);
                          }
                        }}
                        readOnly={!isEditable}
                        style={{
                          fontSize: '0.85rem',
                          color: '#475569',
                          lineHeight: 1.5,
                          width: '100%',
                          minHeight: '80px',
                          border: '1px solid transparent',
                          background: 'transparent',
                          resize: 'vertical',
                          outline: 'none',
                          padding: '0.4rem',
                          borderRadius: '8px',
                          fontFamily: 'inherit',
                          cursor: isEditable ? 'text' : 'not-allowed'
                        }}
                        onFocus={(e) => {
                          if (!isEditable) return;
                          e.target.style.border = '1px solid #e2e8f0';
                          e.target.style.background = '#f8fafc';
                        }}
                        placeholder="Add a detailed description..."
                      />
                      {/* Open Chat Button */}
                      <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '1.25rem', marginTop: '0.5rem' }}>
                        <button
                          onClick={() => {
                            if (activeTask.chat_room_id) {
                              setInitialChatRoomId(activeTask.chat_room_id);
                              setActiveTab('chat');
                              setActiveTask(null);
                            } else {
                              alert('Chat room not ready yet.');
                            }
                          }}
                          style={{
                            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
                            width: '100%', padding: '0.85rem', backgroundColor: '#6366f1', color: '#ffffff',
                            border: 'none', borderRadius: '8px', fontSize: '0.95rem', fontWeight: 600,
                            cursor: 'pointer', transition: 'background-color 0.2s'
                          }}
                          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#4f46e5'}
                          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#6366f1'}
                        >
                          <MessageSquare size={18} /> Chat
                        </button>
                      </div>
                    </div>
                    {/* Detail metadata inline in drawer */}
                    <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                      <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>Task Settings</h3>
                      <div className="task-detail-meta-group">
                        <h4 className="task-detail-meta-label">Status</h4>
                        <select
                          className="task-form-select"
                          style={{ padding: '0.4rem 0.6rem', background: 'white', fontSize: '0.8rem' }}
                          value={activeTask.status}
                          disabled={!isStatusEditable}
                          onChange={async (e) => {
                            try {
                              const newStatus = e.target.value;
                              const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { status: newStatus });
                              setActiveTask(updated);
                              handleLoadTasks();
                              if (newStatus === 'done') {
                                setFeedbackModalConfig({ isOpen: true, taskId: updated.id, taskTitle: updated.title });
                              }
                            } catch (err) {
                              console.error(err);
                              const errMsg = err.response?.data?.error ||
                                err.response?.data?.detail ||
                                (err.response?.data?.status ? (Array.isArray(err.response.data.status) ? err.response.data.status[0] : err.response.data.status) : null) ||
                                'Failed to update task status.';
                              if (errMsg.includes('already has another task In Progress') || errMsg.includes('already has another task') || errMsg.includes('already has another task in progress')) {
                                setWorkloadLimitWarning(errMsg);
                              } else {
                                setError(errMsg);
                              }
                            }
                          }}
                        >
                          <option value="backlog">Backlog</option>
                          <option value="todo">To Do</option>
                          <option value="in_progress">In Progress</option>
                          <option value="in_review">In Review</option>
                          <option value="testing">Testing</option>
                          <option value="done">Done</option>
                        </select>
                      </div>
                      {activeTask.tickets && activeTask.tickets.length > 0 && (
                        <div className="task-detail-meta-group">
                          <h4 className="task-detail-meta-label">Assignee Tickets</h4>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', background: '#f8fafc', padding: '0.6rem', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                            {activeTask.tickets.map(ticket => {
                              const isMyTicket = ticket.assignee_email === currentUserEmail || String(ticket.assignee) === String(currentUserId);
                              const isUserAdminOrOwner = selectedOrg?.my_status?.role === 'owner' || selectedOrg?.my_status?.role === 'admin';
                              const canModifyThisTicket = isMyTicket || isUserAdminOrOwner;
                              return (
                                <div key={ticket.id} style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.78rem' }}>
                                    <span style={{ fontWeight: 600, color: '#334155' }}>
                                      {ticket.assignee_name} {isMyTicket && <span style={{ color: '#6366f1', fontSize: '0.65rem', fontWeight: 'normal' }}>(You)</span>}
                                    </span>
                                  </div>
                                  {canModifyThisTicket ? (
                                    <select
                                      className="task-form-select"
                                      style={{ padding: '0.3rem 0.4rem', background: 'white', fontSize: '0.72rem', marginTop: '0.1rem' }}
                                      value={ticket.status}
                                      onChange={async (e) => {
                                        try {
                                          const updatedTicket = await handleUpdateTicketStatus(ticket.id, e.target.value);
                                          const updatedTickets = activeTask.tickets.map(t => t.id === ticket.id ? { ...t, ...updatedTicket } : t);
                                          setActiveTask({ ...activeTask, tickets: updatedTickets });
                                          // Refetch full task details to stay perfectly synced with backend changes
                                          const updatedTask = await getOrgTaskDetail(selectedOrg.slug, activeTask.id);
                                          setActiveTask(updatedTask);
                                          handleLoadTasks();
                                        } catch (err) {
                                          console.error(err);
                                        }
                                      }}
                                    >
                                      <option value="backlog">Backlog</option>
                                      <option value="todo">To Do</option>
                                      <option value="in_progress">In Progress</option>
                                      <option value="in_review">In Review</option>
                                      <option value="testing">Testing</option>
                                      <option value="done">Done</option>
                                    </select>
                                  ) : (
                                    <span className={`member-role-badge-premium status-${ticket.status}`} style={{ fontSize: '0.65rem', padding: '0.1rem 0.35rem', alignSelf: 'start', marginTop: '0.1rem' }}>
                                      {ticket.status.replace('_', ' ').toUpperCase()}
                                    </span>
                                  )}
                                  <TicketTimer
                                    ticket={ticket}
                                    totalEstimatedMinutes={activeTask.estimated_minutes}
                                    numAssignees={activeTask.tickets.length}
                                  />
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
                      <div className="task-detail-meta-group">
                        <h4 className="task-detail-meta-label">Priority</h4>
                        <select
                          className="task-form-select"
                          style={{ padding: '0.4rem 0.6rem', background: 'white', fontSize: '0.8rem' }}
                          value={activeTask.priority}
                          disabled={!isEditable}
                          onChange={async (e) => {
                            try {
                              const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { priority: e.target.value });
                              setActiveTask(updated);
                              handleLoadTasks();
                            } catch (err) {
                              console.error(err);
                            }
                          }}
                        >
                          <option value="low">Low</option>
                          <option value="medium">Medium</option>
                          <option value="high">High</option>
                        </select>
                      </div>
                      <div className="task-detail-meta-group">
                        <h4 className="task-detail-meta-label">Linked Goal</h4>
                        <select
                          className="task-form-select"
                          style={{ padding: '0.4rem 0.6rem', background: 'white', fontSize: '0.8rem' }}
                          value={activeTask.goal || ''}
                          disabled={!isEditable}
                          onChange={async (e) => {
                            try {
                              const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { goal: e.target.value || null });
                              setActiveTask(updated);
                              handleLoadTasks();
                            } catch (err) {
                              console.error(err);
                            }
                          }}
                        >
                          <option value="">None</option>
                          {goals.map(g => (
                            <option key={g.id} value={g.id}>{g.title}</option>
                          ))}
                        </select>
                      </div>
                    <div className="task-detail-meta-group">
                      <h4 className="task-detail-meta-label">Start Date</h4>
                      <input
                        type="date"
                        className="task-form-input"
                        style={{ padding: '0.4rem 0.6rem', background: 'white', fontSize: '0.8rem' }}
                        value={activeTask.start_date ? activeTask.start_date.substring(0, 10) : ''}
                        disabled={!isEditable}
                        onChange={async (e) => {
                          try {
                            const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { start_date: e.target.value });
                            setActiveTask(updated);
                            handleLoadTasks();
                          } catch (err) {
                            console.error(err);
                          }
                        }}
                      />
                    </div>
                    <div className="task-detail-meta-group">
                      <h4 className="task-detail-meta-label">Due Date</h4>
                      <input
                        type="date"
                        className="task-form-input"
                        style={{ padding: '0.4rem 0.6rem', background: 'white', fontSize: '0.8rem' }}
                        value={activeTask.due_date ? activeTask.due_date.substring(0, 10) : ''}
                        disabled={!isEditable}
                        onChange={async (e) => {
                          try {
                            const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { due_date: e.target.value });
                            setActiveTask(updated);
                            handleLoadTasks();
                          } catch (err) {
                            console.error(err);
                          }
                        }}
                      />
                      {/* Request Extension Button (only for assignees) */}
                      {activeTask.assignee_details && activeTask.assignee_details.some(a => a.email === currentUserEmail) && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            console.log("Opening Extension Modal for task:", activeTask.id);
                            setExtensionModalConfig({ isOpen: true, taskId: activeTask.id, taskTitle: activeTask.title, currentDueDate: activeTask.due_date });
                          }}
                          style={{
                            marginTop: '0.5rem',
                            width: '100%',
                            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
                            padding: '0.4rem', borderRadius: '6px', border: '1px solid #f59e0b',
                            backgroundColor: '#fffbeb', color: '#d97706', fontSize: '0.75rem', fontWeight: 600,
                            cursor: 'pointer', transition: 'all 0.2s'
                          }}
                        >
                          <Calendar size={14} />
                          Request Extension
                        </button>
                      )}
                      {/* Display Extension Requests */}
                      {activeTask.extension_requests && activeTask.extension_requests.length > 0 && (
                        <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                          <h5 style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: '#64748b', margin: 0, fontWeight: 700 }}>Extension History</h5>
                          {activeTask.extension_requests.map(ext => (
                            <div key={ext.id} style={{ fontSize: '0.75rem', padding: '0.5rem', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '6px' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                                <span style={{
                                  fontWeight: 700,
                                  color: ext.status === 'approved' ? '#16a34a' : ext.status === 'rejected' ? '#dc2626' : ext.status === 'modified' ? '#ca8a04' : '#2563eb'
                                }}>
                                  {ext.status.toUpperCase()}
                                </span>
                                <span style={{ color: '#64748b' }}>{new Date(ext.created_at).toLocaleDateString()}</span>
                              </div>
                              <div style={{ color: '#475569', marginBottom: '0.25rem' }}>
                                <strong>Requested Date:</strong> {new Date(ext.proposed_date).toLocaleDateString()}
                              </div>
                              {(ext.status === 'rejected' || ext.status === 'modified') && ext.manager_comment && (
                                <div style={{ padding: '0.4rem', background: '#fee2e2', color: '#991b1b', borderRadius: '4px', marginTop: '0.25rem', border: '1px solid #fecaca' }}>
                                  <strong>Manager Comment:</strong> {ext.manager_comment}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                    
                    {/* Scheduled Start & End (Editable inputs with bidirectional sync) */}
                    <div className="task-detail-meta-group">
                      <h4 className="task-detail-meta-label">Scheduled Start</h4>
                      <input
                        type="datetime-local"
                        className="task-form-input"
                        style={{ padding: '0.4rem 0.6rem', background: 'white', fontSize: '0.8rem' }}
                        value={scheduleToDatetimeLocal(activeTask.planned_start)}
                        disabled={!isEditable}
                        onChange={(e) => {
                          const val = e.target.value ? new Date(e.target.value).toISOString() : null;
                          const assigneeId = activeTask.assignee || activeTask.assignee_id || activeTask.assignee_details?.[0]?.id;
                          const profile = activeTask.assignee_schedule || orgMembers.find(m => String(m.user?.id || m.user_id) === String(assigneeId))?.user?.working_schedule;
                          setActiveTask(prev => ({ ...prev, ...scheduleHandleTimeFieldChange('planned_start', val, prev, profile), _dirtyScheduleField: 'planned_start' }));
                        }}
                      />
                    </div>
                    <div className="task-detail-meta-group">
                      <h4 className="task-detail-meta-label">Scheduled End</h4>
                      <input
                        type="datetime-local"
                        className="task-form-input"
                        style={{ padding: '0.4rem 0.6rem', background: 'white', fontSize: '0.8rem' }}
                        value={scheduleToDatetimeLocal(activeTask.planned_end)}
                        disabled={!isEditable}
                        onChange={(e) => {
                          const val = e.target.value ? new Date(e.target.value).toISOString() : null;
                          const assigneeId = activeTask.assignee || activeTask.assignee_id || activeTask.assignee_details?.[0]?.id;
                          const profile = activeTask.assignee_schedule || orgMembers.find(m => String(m.user?.id || m.user_id) === String(assigneeId))?.user?.working_schedule;
                          setActiveTask(prev => ({ ...prev, ...scheduleHandleTimeFieldChange('planned_end', val, prev, profile), _dirtyScheduleField: 'planned_end' }));
                        }}
                      />
                    </div>
                    {activeTask.schedule_status === 'QUEUED' && (
                      <div className="task-detail-meta-group" style={{ marginTop: '0.25rem' }}>
                        <div style={{
                          padding: '0.5rem 0.75rem',
                          background: '#fffbeb',
                          border: '1px solid #fde68a',
                          borderRadius: '6px',
                          fontSize: '0.75rem',
                          color: '#b45309',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.35rem'
                        }}>
                          <span style={{ display: 'inline-block', width: '6px', height: '6px', borderRadius: '50%', background: '#f59e0b' }}></span>
                          <span>Queued: {activeTask.schedule_reason || 'Waiting For Capacity'}</span>
                        </div>
                      </div>
                    )}
                    {/* Time & Planning Section */}
                    <div className="task-detail-meta-group" style={{ borderTop: '1px solid #f1f5f9', paddingTop: '1rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                        <h4 className="task-detail-meta-label" style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', textTransform: 'uppercase', fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.05em', margin: 0 }}>
                          <Clock size={12} /> Time & Planning
                        </h4>
                        {isEditable && (
                          <button
                            type="button"
                            onClick={async () => {
                              try {
                                // Only send the field the user actually changed so the backend
                                // knows which recalculation to perform (start→end, end→hours, etc.)
                                const payload = {};
                                const dirty = activeTask._dirtyScheduleField;
                                if (dirty === 'planned_start') {
                                  payload.planned_start = activeTask.planned_start;
                                  payload.estimated_hours = activeTask.estimated_hours;
                                  payload.estimated_minutes = activeTask.estimated_minutes;
                                } else if (dirty === 'planned_end') {
                                  payload.planned_end = activeTask.planned_end;
                                } else if (dirty === 'estimated_hours') {
                                  payload.estimated_hours = activeTask.estimated_hours;
                                  payload.estimated_minutes = activeTask.estimated_minutes;
                                } else {
                                  // Fallback: send all fields
                                  payload.planned_start = activeTask.planned_start;
                                  payload.planned_end = activeTask.planned_end;
                                  payload.estimated_hours = activeTask.estimated_hours;
                                  payload.estimated_minutes = activeTask.estimated_minutes;
                                }
                                const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, payload);
                                setActiveTask({ ...updated, _dirtyScheduleField: null });
                                handleLoadTasks();
                              } catch (err) {
                                console.error(err);
                                alert("Failed to save changes");
                              }
                            }}
                            style={{
                              padding: '0.3rem 0.75rem',
                              fontSize: '0.7rem',
                              background: '#6366f1',
                              color: 'white',
                              border: 'none',
                              borderRadius: '6px',
                              cursor: 'pointer',
                              fontWeight: 600,
                              boxShadow: '0 1px 2px rgba(0,0,0,0.1)'
                            }}
                          >
                            Save Changes
                          </button>
                        )}
                      </div>
                      {/* Estimated Time - bidirectional sync removed */}
                      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
                        <div style={{ flex: 1 }}>
                          <label style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600 }}>Est. Hours</label>
                          <input
                            type="number"
                            step="0.1"
                            min="0"
                            placeholder="0.0"
                            className="task-form-input"
                            style={{ padding: '0.4rem 0.6rem', background: 'white', fontSize: '0.8rem' }}
                            value={activeTask.estimated_hours || ''}
                            disabled={!isEditable}
                            onChange={(e) => {
                              const val = e.target.value === '' ? null : parseFloat(e.target.value);
                              const assigneeId = activeTask.assignee || activeTask.assignee_id || activeTask.assignee_details?.[0]?.id;
                              const profile = activeTask.assignee_schedule || orgMembers.find(m => String(m.user?.id || m.user_id) === String(assigneeId))?.user?.working_schedule;
                              setActiveTask(prev => ({ ...prev, ...scheduleHandleTimeFieldChange('estimated_hours', val, prev, profile), _dirtyScheduleField: 'estimated_hours' }));
                            }}
                          />
                        </div>
                        <div style={{ flex: 1 }}>
                          <label style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600 }}>Est. Minutes <span style={{ fontStyle: 'italic', fontWeight: 400 }}>(auto)</span></label>
                          <input
                            type="number"
                            min="0"
                            placeholder="0"
                            className="task-form-input"
                            style={{ padding: '0.4rem 0.6rem', background: '#f8fafc', fontSize: '0.8rem', color: '#64748b' }}
                            value={activeTask.estimated_minutes != null ? activeTask.estimated_minutes : (activeTask.estimated_hours ? Math.round(activeTask.estimated_hours * 60) : '')}
                            readOnly
                            tabIndex={-1}
                          />
                        </div>
                      </div>
                      {/* Actual Time Spent */}
                      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
                        <div style={{ flex: 1 }}>
                          <label style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600 }}>
                            Actual Hours {activeTask.tickets && activeTask.tickets.length > 0 && '(Auto)'}
                          </label>
                          <input
                            type="number"
                            step="0.1"
                            min="0"
                            placeholder="0.0"
                            className="task-form-input"
                            style={{ padding: '0.4rem 0.6rem', background: activeTask.tickets && activeTask.tickets.length > 0 ? '#f1f5f9' : 'white', fontSize: '0.8rem' }}
                            value={activeTask.tickets && activeTask.tickets.length > 0 ? (liveActualMins / 60).toFixed(2) : (activeTask.actual_hours || '')}
                            disabled={!isEditable || (activeTask.tickets && activeTask.tickets.length > 0)}
                            onChange={async (e) => {
                              const val = e.target.value === '' ? null : parseFloat(e.target.value);
                              setActiveTask({ ...activeTask, actual_hours: val });
                            }}
                            onBlur={async (e) => {
                              try {
                                const val = e.target.value === '' ? null : parseFloat(e.target.value);
                                const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { actual_hours: val });
                                setActiveTask(updated);
                                handleLoadTasks();
                              } catch (err) {
                                console.error(err);
                              }
                            }}
                          />
                        </div>
                        <div style={{ flex: 1 }}>
                          <label style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600 }}>
                            Actual Mins {activeTask.tickets && activeTask.tickets.length > 0 && '(Auto)'}
                          </label>
                          <input
                            type="number"
                            min="0"
                            placeholder="0"
                            className="task-form-input"
                            style={{ padding: '0.4rem 0.6rem', background: activeTask.tickets && activeTask.tickets.length > 0 ? '#f1f5f9' : 'white', fontSize: '0.8rem' }}
                            value={activeTask.tickets && activeTask.tickets.length > 0 ? Math.floor(liveActualMins) : (activeTask.actual_time_spent_minutes || '')}
                            disabled={!isEditable || (activeTask.tickets && activeTask.tickets.length > 0)}
                            onChange={async (e) => {
                              const val = e.target.value === '' ? null : parseInt(e.target.value, 10);
                              setActiveTask({ ...activeTask, actual_time_spent_minutes: val });
                            }}
                            onBlur={async (e) => {
                              try {
                                const val = e.target.value === '' ? null : parseInt(e.target.value, 10);
                                const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { actual_time_spent_minutes: val });
                                setActiveTask(updated);
                                handleLoadTasks();
                              } catch (err) {
                                console.error(err);
                              }
                            }}
                          />
                        </div>
                      </div>
                    </div>
                    {/* Assignees Section */}
                    <div className="task-detail-meta-group" style={{ borderTop: '1px solid #f1f5f9', paddingTop: '1rem' }}>
                      <h4 className="task-detail-meta-label" style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', textTransform: 'uppercase', fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.05em' }}>
                        <Users size={14} /> Assignees
                      </h4>
                      <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem', boxShadow: '0 1px 2px rgba(0,0,0,0.02)' }}>
                        {activeTask.assignee_details?.length > 0 ? (
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', marginBottom: '0.5rem' }}>
                            {activeTask.assignee_details.map(u => (
                              <div key={u.id} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem', color: '#334155', background: '#f1f5f9', padding: '0.2rem 0.5rem', borderRadius: '999px' }}>
                                <div style={{
                                  width: '16px',
                                  height: '16px',
                                  borderRadius: '50%',
                                  background: 'linear-gradient(135deg, #6366f1, #a855f7)',
                                  color: 'white',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  fontSize: '0.55rem',
                                  fontWeight: 'bold'
                                }}>
                                  {u.first_name?.[0] || u.email[0].toUpperCase()}
                                </div>
                                <span>{u.first_name || u.email}</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <span style={{ fontSize: '0.8rem', color: '#94a3b8', fontStyle: 'italic', marginBottom: '0.5rem' }}>Unassigned</span>
                        )}
                        <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b' }}>Assignee Allocation:</div>
                          {/* Commented: Smart Suggestion Feature
                               <div style={{ display: 'flex', border: '1px solid #cbd5e1', borderRadius: '8px', overflow: 'hidden', width: 'fit-content', marginBottom: '0.25rem' }}>
                                 <button
                                   type="button"
                                   onClick={() => setEditAssignMode('manual')}
                                   style={{
                                     padding: '0.3rem 0.75rem',
                                     fontSize: '0.75rem',
                                     border: 'none',
                                     background: editAssignMode === 'manual' ? '#6366f1' : 'white',
                                     color: editAssignMode === 'manual' ? 'white' : '#475569',
                                     fontWeight: 500,
                                     cursor: 'pointer',
                                     transition: 'all 0.2s'
                                   }}
                                 >
                                   Manual Assign
                                 </button>
                                 <button
                                   type="button"
                                   onClick={async () => {
                                     setEditAssignMode('suggest');
                                     setEditSmartSuggestLoading(true);
                                     setEditSmartSuggestError(null);
                                     try {
                                       const params = {
                                         estimated_hours: activeTask.estimated_hours || 1.0,
                                         priority: activeTask.priority || 'medium',
                                         impact: activeTask.impact || 5,
                                         risk: activeTask.risk || 'medium'
                                       };
                                       const response = await getSmartSuggest(selectedOrg.id, params);
                                       setEditSmartSuggestions(response.suggestions || []);
                                     } catch (err) {
                                       console.error(err);
                                       setEditSmartSuggestError("Failed to fetch suggestions.");
                                     } finally {
                                       setEditSmartSuggestLoading(false);
                                     }
                                   }}
                                   style={{
                                     padding: '0.3rem 0.75rem',
                                     fontSize: '0.75rem',
                                     border: 'none',
                                     background: editAssignMode === 'suggest' ? '#6366f1' : 'white',
                                     color: editAssignMode === 'suggest' ? 'white' : '#475569',
                                     fontWeight: 500,
                                     cursor: 'pointer',
                                     transition: 'all 0.2s'
                                   }}
                                 >
                                   Smart Suggest
                                 </button>
                               </div>
                               */}
                          {editAssignMode === 'manual' ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                              <select
                                style={{
                                  padding: '0.4rem',
                                  borderRadius: '6px',
                                  border: '1px solid #cbd5e1',
                                  fontSize: '0.8rem',
                                  color: '#334155',
                                  outline: 'none',
                                  width: '100%'
                                }}
                                value={(activeTask.assignees || activeTask.assignee_details?.map(d => d.id) || [])[0] || ''}
                                onChange={async (e) => {
                                  const val = e.target.value;
                                  try {
                                    const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { assignees: val ? [val] : [] });
                                    setActiveTask(updated);
                                    handleLoadTasks();
                                  } catch (err) {
                                    console.error("Failed to update assignees:", err);
                                  }
                                }}
                              >
                                <option value="">Unassigned</option>
                                {orgMembers.map(m => {
                                  const userId = m.user?.id || m.user_id;
                                  const name = m.user?.first_name || m.user?.last_name ? `${m.user.first_name || ''} ${m.user.last_name || ''}`.trim() : m.email;
                                  return (
                                    <option key={userId} value={userId}>
                                      {name}
                                    </option>
                                  );
                                })}
                              </select>
                              {null}
                            </div>
                          ) : (
                            /* Commented: Smart Suggestion Feature */
                            false && (
                              <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                {editSmartSuggestLoading ? (
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.76rem', color: '#64748b' }}>
                                    <div style={{ border: '2px solid #f3f3f3', borderTop: '2px solid #6366f1', borderRadius: '50%', width: '14px', height: '14px', animation: 'spin 1s linear infinite' }} />
                                    <span>Analyzing matches...</span>
                                  </div>
                                ) : editSmartSuggestError ? (
                                  <span style={{ fontSize: '0.76rem', color: '#ef4444' }}>{editSmartSuggestError}</span>
                                ) : editSmartSuggestions.length === 0 ? (
                                  <span style={{ fontSize: '0.76rem', color: '#64748b', fontStyle: 'italic' }}>No members available to suggest</span>
                                ) : (
                                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                    {editSmartSuggestions.map((sugg, idx) => {
                                      const currentAssigneeIds = activeTask.assignees || activeTask.assignee_details?.map(d => d.id) || [];
                                      const isSelected = currentAssigneeIds[0] === sugg.id;
                                      return (
                                        <div
                                          key={sugg.id}
                                          style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'space-between',
                                            padding: '0.5rem 0.6rem',
                                            background: isSelected ? '#f5f7ff' : 'white',
                                            border: isSelected ? '1px solid #6366f1' : '1px solid #e2e8f0',
                                            borderRadius: '6px',
                                            gap: '0.5rem'
                                          }}
                                        >
                                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem', flex: 1 }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', flexWrap: 'wrap' }}>
                                              <span style={{ fontWeight: 700, fontSize: '0.78rem', color: '#1e293b' }}>{sugg.name || sugg.email}</span>
                                              {sugg.is_busy ? (
                                                <span style={{ background: '#fee2e2', color: '#b91c1c', border: '1px solid #fca5a5', fontSize: '0.58rem', padding: '0.02rem 0.2rem', borderRadius: '3px', fontWeight: 600 }}>BUSY</span>
                                              ) : (
                                                <span style={{ background: '#ecfdf5', color: '#047857', border: '1px solid #6ee7b7', fontSize: '0.58rem', padding: '0.02rem 0.2rem', borderRadius: '3px', fontWeight: 600 }}>FREE</span>
                                              )}
                                            </div>
                                            {sugg.email && sugg.name && (
                                              <span style={{ fontSize: '0.69rem', color: '#94a3b8' }}>✉ {sugg.email}</span>
                                            )}
                                            <span style={{ fontSize: '0.7rem', color: '#475569', display: 'flex', alignItems: 'center', gap: '0.15rem', flexWrap: 'wrap' }}>
                                              <Award size={10} style={{ color: '#fbbf24' }} /> Match Score: <strong>{sugg.match_score}</strong>
                                              <span style={{ color: '#cbd5e1' }}>|</span>
                                              <span style={{ fontStyle: 'italic', color: '#64748b' }}>{sugg.reason}</span>
                                            </span>
                                            {sugg.is_busy && isSelected && (
                                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: '#b45309', fontSize: '0.7rem', marginTop: '0.1rem' }}>
                                                <AlertCircle size={11} />
                                                <span>{sugg.name} is working on another task.</span>
                                              </div>
                                            )}
                                          </div>
                                          <button
                                            type="button"
                                            onClick={async () => {
                                              try {
                                                const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { assignees: [sugg.id] });
                                                setActiveTask(updated);
                                                handleLoadTasks();
                                              } catch (err) {
                                                console.error("Failed to assign suggested member:", err);
                                              }
                                            }}
                                            disabled={isSelected}
                                            style={{
                                              padding: '0.25rem 0.6rem',
                                              fontSize: '0.72rem',
                                              width: 'auto',
                                              borderRadius: '50px',
                                              cursor: isSelected ? 'default' : 'pointer',
                                              border: '1px solid',
                                              borderColor: isSelected ? '#e2e8f0' : '#6366f1',
                                              background: isSelected ? '#f1f5f9' : '#6366f1',
                                              color: isSelected ? '#94a3b8' : 'white',
                                              fontWeight: 500,
                                              transition: 'all 0.2s',
                                              whiteSpace: 'nowrap'
                                            }}
                                          >
                                            {isSelected ? 'Assigned' : 'Use'}
                                          </button>
                                        </div>
                                      );
                                    })}
                                  </div>
                                )}
                              </div>
                            )
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="task-detail-meta-group">
                      <h4 className="task-detail-meta-label">Sharing Settings</h4>
                      <button
                        type="button"
                        onClick={() => openSharingModal('activeTask', {
                          ...activeTask,
                          assignees: (activeTask.assignees || []).map(a => a.id || a.user_id || a),
                          shared_viewers: (activeTask.shared_viewers || []).map(v => v.id || v.user_id || v)
                        })}
                        style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 0.6rem', background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '8px', cursor: 'pointer', color: '#334155', fontWeight: 500, justifyContent: 'space-between', width: '100%', outline: 'none' }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <Users size={13} style={{ color: '#6366f1' }} />
                          <span style={{ fontSize: '0.75rem' }}>
                            {activeTask.sharing_option === 'private' ? 'Private' : activeTask.sharing_option === 'specific' ? 'Specific People' : 'Entire Workspace'}
                          </span>
                        </div>
                      </button>
                    </div>
                    <div style={{ marginTop: '0.75rem', paddingTop: '1rem', borderTop: '1px solid #e2e8f0' }}>
                      <button
                        type="button"
                        className="danger-btn-premium"
                        style={{ width: '100%', justifyContent: 'center', padding: '0.45rem', fontSize: '0.78rem' }}
                        onClick={() => {
                          modal.showConfirmation('Are you sure you want to delete this task?', async () => {
                            try {
                              await deleteOrgTask(selectedOrg.slug, activeTask.id);
                              modal.showSuccess('Task deleted successfully');
                              setTasksView('list');
                              handleLoadTasks();
                            } catch (err) {
                              modal.showError("Failed to delete task or access denied.");
                            }
                          });
                        }}
                      >
                        <Trash2 size={11} style={{ marginRight: '0.4rem' }} /> Delete Task
                      </button>
                    </div>
                  </div>
                </div>
                  </div>
        );
              };
        if (tasksView === 'list' || tasksView === 'detail') {
                const filteredTasks = (Array.isArray(tasks) ? tasks : []).filter(task => {
                  const goalObj = (goals || []).find(g => g.id === task.goal);
        const goalTitle = goalObj ? goalObj.title : '';
        const matchesSearch = (task.title || '').toLowerCase().includes(taskSearchQuery.toLowerCase()) ||
        (task.description || '').toLowerCase().includes(taskSearchQuery.toLowerCase()) ||
        (goalTitle || '').toLowerCase().includes(taskSearchQuery.toLowerCase());
        let matchesStatus = false;
        if (taskStatusFilter === 'all') {
          matchesStatus = true;
                  } else if (taskStatusFilter === 'overdue') {
                    const isActuallyOverdue = task.due_date && new Date(task.due_date) < new Date();
        matchesStatus = (task.is_overdue || isActuallyOverdue) && task.status !== 'done';
                  } else {
          matchesStatus = task.status === taskStatusFilter;
                  }
        const matchesPriority = taskPriorityFilter === 'all' || task.priority === taskPriorityFilter;
                  const hasAssignee = task.assignee_details && task.assignee_details.length > 0;
        return matchesSearch && matchesStatus && matchesPriority && hasAssignee;
                });
                const doneCount = (Array.isArray(tasks) ? tasks : []).filter(t => t.status === 'done').length;
        const totalCount = (Array.isArray(tasks) ? tasks : []).length;
                const progressPct = totalCount > 0 ? Math.round((doneCount / totalCount) * 100) : 0;
                const renderListView = () => {
                  if (filteredTasks.length === 0) {
                    return (
        <div className="premium-card-settings" style={{ padding: '3rem', textAlign: 'center' }}>
          <Inbox size={48} style={{ color: '#cbd5e1', marginBottom: '1rem' }} />
          <p style={{ fontSize: '1.1rem', fontWeight: 600, color: '#1e293b', marginBottom: '0.25rem' }}>No assigned tasks found</p>
          <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '1rem' }}>Only tasks with at least one assigned member are shown. Try adjusting your filters.</p>
          <button
            onClick={() => { setTaskSearchQuery(''); setTaskStatusFilter('all'); setTaskPriorityFilter('all'); }}
            className="btn-secondary"
            style={{ width: 'auto', padding: '0.5rem 1rem', fontSize: '0.85rem' }}
          >
            <RefreshCw size={12} style={{ marginRight: '0.4rem' }} /> Reset Filters
          </button>
        </div>
        );
                  }
        return (
        <div className="premium-card-settings" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table className="task-table-premium">
              <thead>
                <tr>
                  <th style={{ paddingLeft: '1.5rem', width: '45%' }}>Task Title</th>
                  <th style={{ textAlign: 'center' }}>Status</th>
                  <th style={{ textAlign: 'center' }}>Priority</th>
                  <th style={{ textAlign: 'center' }}>Due Date</th>
                  <th style={{ textAlign: 'center' }}>Assignees</th>
                  <th style={{ textAlign: 'center', width: '80px' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredTasks.map(task => {
                  return (
                    <tr key={task.id} className="task-row-premium">
                      <td style={{ paddingLeft: '1.5rem', borderLeft: `4px solid ${task.status === 'done' ? '#10b981' : task.status === 'in_progress' ? '#6366f1' : task.status === 'in_review' ? '#f59e0b' : task.status === 'todo' ? '#0ea5e9' : '#94a3b8'}` }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                          <div
                            style={{ fontWeight: 600, color: '#0f172a', cursor: 'pointer', transition: 'color 0.2s' }}
                            onClick={() => handleTaskClick(task)}
                            onMouseEnter={(e) => e.target.style.color = '#6366f1'}
                            onMouseLeave={(e) => e.target.style.color = '#0f172a'}
                          >
                            {task.title}
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <span className="member-role-badge-premium role-low" style={{ textTransform: 'uppercase', fontSize: '0.6rem', padding: '0.1rem 0.35rem' }}>
                              {task.issue_type}
                            </span>
                            {(() => {
                              const goalObj = (goals || []).find(g => g.id === task.goal);
                              if (goalObj) {
                                return (
                                  <span className="member-role-badge-premium role-medium" style={{ textTransform: 'none', fontSize: '0.6rem', padding: '0.1rem 0.35rem', background: '#e0f2fe', color: '#0369a1', borderColor: '#bae6fd' }} title={`Goal: ${goalObj.title}`}>
                                    🎯 {goalObj.title}
                                  </span>
                                );
                              }
                              return null;
                            })()}
                            {task.description && (
                              <span style={{ fontSize: '0.75rem', color: '#94a3b8', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '250px' }}>
                                {task.description}
                              </span>
                            )}
                          </div>
                        </div>
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <span className={`member-role-badge-premium status-${task.status}`}>
                          {task.status.replace('_', ' ').toUpperCase()}
                        </span>
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <span className={`member-role-badge-premium role-${task.priority === 'high' ? 'high' : task.priority === 'medium' ? 'medium' : 'low'}`}>
                          {task.priority.toUpperCase()}
                        </span>
                      </td>
                      <td style={{ textAlign: 'center', fontSize: '0.8rem', color: '#64748b' }}>
                        {task.due_date ? (
                          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
                            <Calendar size={12} />
                            <span>{new Date(task.due_date).toLocaleDateString()}</span>
                          </div>
                        ) : '-'}
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.25rem' }}>
                          {task.assignee_details && task.assignee_details.length > 0 ? (
                            task.assignee_details.map((u, idx) => (
                              <div
                                key={u.id || idx}
                                title={u.first_name || u.email}
                                style={{
                                  width: '24px',
                                  height: '24px',
                                  borderRadius: '50%',
                                  background: 'linear-gradient(135deg, #6366f1, #a855f7)',
                                  color: 'white',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  fontSize: '0.65rem',
                                  fontWeight: 'bold',
                                  border: '1.5px solid white',
                                  boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
                                }}
                              >
                                {u.first_name?.[0] || u.email[0].toUpperCase()}
                              </div>
                            ))
                          ) : (
                            <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontStyle: 'italic' }}>None</span>
                          )}
                        </div>
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <button
                          onClick={() => handleTaskClick(task)}
                          className="text-btn"
                          style={{ padding: '0.3rem', borderRadius: '6px' }}
                        >
                          <ChevronRight size={16} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
        );
                };
                const renderBoardView = () => {
                  const columns = [
        {id: 'backlog', name: 'Backlog', color: '#94a3b8' },
        {id: 'todo', name: 'To Do', color: '#0ea5e9' },
        {id: 'in_progress', name: 'In Progress', color: '#6366f1' },
        {id: 'in_review', name: 'In Review', color: '#f59e0b' },
        {id: 'testing', name: 'Testing', color: '#ec4899' },
        {id: 'done', name: 'Done', color: '#10b981' }
        ];
                  // Filter Kanban tickets based on search and priority filter
                  const filteredTickets = (Array.isArray(kanbanTickets) ? kanbanTickets : []).filter(ticket => {
                    const t = ticket.task_details || { };
        const goalTitle = t.goal_title || '';
        const assigneeName = ticket.assignee_details?.name || '';
        const matchesSearch = (t.title || '').toLowerCase().includes(taskSearchQuery.toLowerCase()) ||
        (t.description || '').toLowerCase().includes(taskSearchQuery.toLowerCase()) ||
        (goalTitle || '').toLowerCase().includes(taskSearchQuery.toLowerCase()) ||
        (assigneeName || '').toLowerCase().includes(taskSearchQuery.toLowerCase());
        const matchesPriority = taskPriorityFilter === 'all' || t.priority === taskPriorityFilter;
        return matchesSearch && matchesPriority;
                  });
        return (
        <div className="task-board-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '1rem', overflowX: 'auto', paddingBottom: '1rem', minHeight: '500px', alignItems: 'start' }}>
          {columns.map(col => {
            const colTickets = filteredTickets.filter(t => t.status === col.id);
            return (
              <div
                key={col.id}
                className="task-board-column"
                style={{
                  background: '#f8fafc',
                  borderRadius: '16px',
                  padding: '1rem',
                  minHeight: '480px',
                  border: '1px solid #e2e8f0',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                  transition: 'all 0.2s',
                }}
                onDragOver={(e) => {
                  e.preventDefault();
                  e.currentTarget.style.background = '#f1f5f9';
                  e.currentTarget.style.borderColor = col.color;
                }}
                onDragLeave={(e) => {
                  e.currentTarget.style.background = '#f8fafc';
                  e.currentTarget.style.borderColor = '#e2e8f0';
                }}
                onDrop={async (e) => {
                  e.preventDefault();
                  e.currentTarget.style.background = '#f8fafc';
                  e.currentTarget.style.borderColor = '#e2e8f0';
                  const ticketId = e.dataTransfer.getData('text/plain');
                  if (ticketId) {
                    await handleUpdateTicketStatus(ticketId, col.id);
                  }
                }}
              >
                <div className="task-board-column-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', paddingBottom: '0.5rem', borderBottom: `2px solid ${col.color}` }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      backgroundColor: col.color
                    }} />
                    <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#1e293b', margin: 0 }}>{col.name}</h4>
                  </div>
                  <span style={{ fontSize: '0.7rem', fontWeight: 'bold', color: col.color, background: 'white', border: `1.5px solid ${col.color}`, padding: '0.1rem 0.5rem', borderRadius: '999px' }}>
                    {colTickets.length}
                  </span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', overflowY: 'auto', maxHeight: '550px', paddingRight: '2px', flex: 1 }}>
                  {colTickets.length === 0 ? (
                    <div style={{ border: '1.5px dashed #cbd5e1', borderRadius: '12px', padding: '2rem 1rem', textAlign: 'center', fontSize: '0.75rem', color: '#94a3b8', background: 'white' }}>
                      Drag tasks here
                    </div>
                  ) : (
                    colTickets.map(ticket => {
                      const task = ticket.task_details || {};
                      const assignee = ticket.assignee_details || {};
                      return (
                        <div
                          key={ticket.id}
                          draggable={true}
                          onDragStart={(e) => {
                            e.dataTransfer.setData('text/plain', ticket.id);
                            e.currentTarget.style.opacity = '0.5';
                          }}
                          onDragEnd={(e) => {
                            e.currentTarget.style.opacity = '1';
                          }}
                          onClick={() => handleTaskClick({ id: ticket.task })}
                          className="task-card-premium"
                          style={{
                            borderLeft: `4px solid ${col.color}`,
                            cursor: 'grab',
                            background: 'white',
                            borderRadius: '12px',
                            padding: '0.85rem',
                            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)',
                            border: '1px solid #e2e8f0',
                            borderLeftWidth: '4px',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '0.6rem',
                            transition: 'transform 0.15s, box-shadow 0.15s'
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.transform = 'translateY(-2px)';
                            e.currentTarget.style.boxShadow = '0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04)';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.transform = 'translateY(0)';
                            e.currentTarget.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)';
                          }}
                        >
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span style={{ fontSize: '0.6rem', fontWeight: 700, color: col.color, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                {task.issue_type}
                              </span>
                              <span className={`member-role-badge-premium role-${task.priority === 'high' ? 'high' : task.priority === 'medium' ? 'medium' : 'low'}`} style={{ fontSize: '0.55rem', padding: '0.05rem 0.35rem' }}>
                                {task.priority?.toUpperCase()}
                              </span>
                            </div>
                            <h5 style={{ fontWeight: 700, color: '#0f172a', fontSize: '0.85rem', margin: 0, lineHeight: 1.35 }}>
                              {task.title}
                            </h5>
                          </div>
                          {task.description && (
                            <p style={{ fontSize: '0.75rem', color: '#64748b', margin: 0, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden', textOverflow: 'ellipsis', lineHeight: 1.4 }}>
                              {task.description}
                            </p>
                          )}
                          {task.goal_title && (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.65rem', color: '#6366f1', background: '#e0e7ff', padding: '0.15rem 0.4rem', borderRadius: '4px', alignSelf: 'start', fontWeight: 600 }}>
                              <Target size={10} />
                              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '120px' }}>{task.goal_title}</span>
                            </div>
                          )}
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '0.5rem', borderTop: '1px solid #f1f5f9', marginTop: '0.25rem' }}>
                            {task.due_date ? (
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.2rem', fontSize: '0.68rem', color: new Date(task.due_date) < new Date() ? '#ef4444' : '#64748b', fontWeight: 500 }}>
                                <Calendar size={11} />
                                <span>{new Date(task.due_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}</span>
                              </div>
                            ) : (
                              <span style={{ fontSize: '0.65rem', color: '#cbd5e1', fontStyle: 'italic' }}>No due date</span>
                            )}
                            {assignee.email && (
                              <div
                                title={assignee.name || assignee.email}
                                style={{
                                  width: '24px',
                                  height: '24px',
                                  borderRadius: '50%',
                                  background: 'linear-gradient(135deg, #6366f1, #a855f7)',
                                  color: 'white',
                                  border: '1.5px solid white',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  fontSize: '0.65rem',
                                  fontWeight: 800,
                                  boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
                                }}
                              >
                                {assignee.initial || assignee.email[0].toUpperCase()}
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            );
          })}
        </div>
        );
                };
        return (
        <div className="task-hub-container">
          {/* Header */}
          <div className="task-header-premium">
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>Workspace Tasks</h3>
                <span className="member-role-badge-premium status-in-progress" style={{ fontSize: '0.65rem' }}>
                  {filteredTasks.length} active
                </span>
              </div>
              <p style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.25rem' }}>Manage, organize, and track your workspace deliverables.</p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div className="task-layout-toggle">
                <button
                  onClick={() => setTasksLayout('list')}
                  className={`task-layout-btn ${tasksLayout === 'list' ? 'active' : ''}`}
                  title="List Layout"
                >
                  <List size={14} />
                </button>
                <button
                  onClick={() => setTasksLayout('board')}
                  className={`task-layout-btn ${tasksLayout === 'board' ? 'active' : ''}`}
                  title="Kanban Board Layout"
                >
                  <Grid size={14} />
                </button>
              </div>
              {(selectedOrg?.my_status?.role === 'owner' || selectedOrg?.my_status?.role === 'admin') && (
                <>

                  <button
                    onClick={() => setIsExtensionRequestsModalOpen(true)}
                    className="btn-secondary"
                    style={{
                      width: 'auto', padding: '0 1.2rem', fontSize: '0.85rem',
                      display: 'flex', alignItems: 'center', gap: '0.5rem',
                      position: 'relative', height: '36px', margin: 0,
                      backgroundColor: '#fff', border: '1px solid #e2e8f0', color: '#0f172a',
                      borderRadius: '8px'
                    }}
                  >
                    <Calendar size={14} />
                    <span style={{ fontWeight: 600 }}>Extension Requests</span>
                    {pendingExtensionCount > 0 && (
                      <span style={{
                        position: 'absolute', top: '-6px', right: '-6px',
                        backgroundColor: '#ef4444', color: 'white',
                        fontSize: '0.65rem', fontWeight: 700,
                        width: '18px', height: '18px', display: 'flex',
                        alignItems: 'center', justifyContent: 'center',
                        borderRadius: '50%', boxShadow: '0 0 0 2px #fff'
                      }}>
                        {pendingExtensionCount}
                      </span>
                    )}
                  </button>
                </>
              )}
              {/* Commented: Smart Suggestion Feature
                        {(selectedOrg?.my_status?.role === 'owner' || selectedOrg?.my_status?.role === 'admin') && (
                          <button
                            onClick={() => setIsFreeMembersModalOpen(true)}
                            className="btn-secondary"
                            style={{ 
                              width: 'auto', padding: '0 1.2rem', fontSize: '0.85rem', 
                              display: 'flex', alignItems: 'center', gap: '0.5rem', 
                              height: '36px', margin: '0 0.5rem 0 0',
                              backgroundColor: '#fff', border: '1px solid #e2e8f0', color: '#0f172a',
                              borderRadius: '8px'
                            }}
                          >
                            <Users size={14} /> 
                            <span style={{ fontWeight: 600 }}>Check Free Members Now</span>
                          </button>
                        )}
                        */}


              <button
                onClick={() => setTasksView('create')}
                className="btn-primary"
                style={{ width: 'auto', padding: '0 1.2rem', fontSize: '0.85rem', height: '36px', margin: 0, display: 'flex', alignItems: 'center', borderRadius: '8px' }}
              >
                <Plus size={14} style={{ marginRight: '0.4rem' }} /> Create Task
              </button>
            </div>
          </div>
          {/* Progress Stats */}
          {totalCount > 0 && (
            <div className="task-progress-card">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{ background: 'rgba(99, 102, 241, 0.1)', color: '#6366f1', width: '36px', height: '36px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <ListTodo size={18} />
                </div>
                <div>
                  <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>Workspace Goal Progress</h4>
                  <p style={{ fontSize: '0.75rem', color: '#64748b', margin: 0 }}>{doneCount} of {totalCount} tasks completed</p>
                </div>
              </div>
              <div style={{ flex: 1, maxWidth: '400px', display: 'flex', alignItems: 'center', gap: '0.75rem', justifyContent: 'flex-end' }}>
                <div className="task-progress-bar-bg">
                  <div className="task-progress-bar-fill" style={{ width: `${progressPct}%` }} />
                </div>
                <span style={{ fontSize: '0.8rem', fontWeight: 'bold', color: '#6366f1' }}>{progressPct}%</span>
              </div>
            </div>
          )}
          {/* Filter and Search Bar */}
          <div className="task-filter-bar">
            <div className="task-search-wrapper">
              <Search size={14} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
              <input
                type="text"
                placeholder="Search task title or description..."
                value={taskSearchQuery}
                onChange={(e) => setTaskSearchQuery(e.target.value)}
                className="task-search-input"
              />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem', color: '#64748b' }}>
                <Filter size={12} />
                <span>Filters:</span>
              </div>
              <select
                value={taskStatusFilter}
                onChange={(e) => setTaskStatusFilter(e.target.value)}
                className="task-select-filter"
              >
                <option value="all">Status: All</option>
                <option value="overdue">Overdue</option>
                <option value="backlog">Backlog</option>
                <option value="todo">To Do</option>
                <option value="in_progress">In Progress</option>
                <option value="in_review">In Review</option>
                <option value="testing">Testing</option>
                <option value="done">Done</option>
              </select>
              <select
                value={taskPriorityFilter}
                onChange={(e) => setTaskPriorityFilter(e.target.value)}
                className="task-select-filter"
              >
                <option value="all">Priority: All</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
              {(taskSearchQuery || taskStatusFilter !== 'all' || taskPriorityFilter !== 'all') && (
                <button
                  onClick={() => { setTaskSearchQuery(''); setTaskStatusFilter('all'); setTaskPriorityFilter('all'); }}
                  className="text-btn"
                  style={{ fontSize: '0.8rem' }}
                >
                  Clear
                </button>
              )}
            </div>
          </div>
          {/* View render */}
          <div style={{ display: 'flex', gap: '1rem', width: '100%', minHeight: '600px', position: 'relative' }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              {tasksLayout === 'list' ? renderListView() : renderBoardView()}
            </div>
            {tasksView === 'detail' && activeTask && renderTaskDetailDrawer()}
          </div>
        </div>
        );
              }
        if (tasksView === 'create') {
                return (
        <div className="task-form-container">
          <button
            onClick={() => setTasksView('list')}
            className="back-btn-premium"
          >
            <ArrowLeft size={16} /> Back to Tasks
          </button>
          <div className="task-form-card">
            <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0f172a', margin: '0 0 0.5rem 0' }}>Create New Task</h2>
            {error && (
              <div className="error-message" style={{ padding: '0.75rem', background: '#fef2f2', border: '1px solid #fee2e2', borderRadius: '6px', color: '#b91c1c', fontSize: '0.85rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <AlertCircle size={16} />
                <span>{error}</span>
              </div>
            )}
            <form style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }} onSubmit={async (e) => {
              e.preventDefault();
              setLoading(true);
              setError('');
              try {
                const payload = {
                  ...newTaskData,
                  organization: selectedOrg.id
                };
                // Remove empty strings which cause Django validation errors
                if (!payload.goal) delete payload.goal;
                if (!payload.due_date) delete payload.due_date;
                if (!payload.start_date) delete payload.start_date;
                if (!payload.due_time) delete payload.due_time;
                if (!payload.estimated_minutes) delete payload.estimated_minutes;
                if (!payload.estimated_hours) delete payload.estimated_hours;
                if (!payload.reminder_preference) delete payload.reminder_preference;
                if (payload.reminder_preference !== 'custom' || !payload.reminder_duration_minutes) {
                  delete payload.reminder_duration_minutes;
                }
                const response = await createOrgTask(selectedOrg.slug, payload);
                modal.showSuccess(formatTaskCreateSuccess(response));
                setTasksView('list');
                setNewTaskData({
                  title: '', description: '', issue_type: 'task', priority: 'medium',
                  status: 'todo', due_date: '', start_date: '', estimated_hours: '', assignees: [],
                  watchers: [], visibility_type: 'specific', visible_to: [], goal: '',
                  sharing_option: 'specific', shared_viewers: [],
                  due_time: '', estimated_minutes: '', reminder_preference: 'none', reminder_duration_minutes: '',
                  required_assignees: 1,
                  impact: 5,
                  risk: 'medium'
                });
                handleLoadTasks();
              } catch (err) {
                console.error("Error creating task:", err.response?.data || err);
                let errorMessage = err.response?.data?.error || err.response?.data?.detail || "Failed to create task";
                if (err.response?.data && typeof err.response.data === 'object' && !err.response.data.error && !err.response.data.detail) {
                  errorMessage = Object.entries(err.response.data).map(([k, v]) => `${k}: ${v}`).join(', ');
                }
                if (errorMessage.includes('already has another task In Progress') || errorMessage.includes('already has another task') || errorMessage.includes('already has another task in progress')) {
                  setWorkloadLimitWarning(errorMessage);
                } else {
                  modal.showError(errorMessage);
                }
              } finally {
                setLoading(false);
              }
            }}>
              <div className="task-form-group">
                <label className="task-form-label">Task Title</label>
                <input
                  type="text"
                  required
                  className="task-form-input"
                  placeholder="What needs to be done?"
                  value={newTaskData.title}
                  onChange={(e) => setNewTaskData({ ...newTaskData, title: e.target.value })}
                />
              </div>
              <div className="task-form-group">
                <label className="task-form-label">Description</label>
                <textarea
                  rows={4}
                  className="task-form-input"
                  style={{ resize: 'vertical', minHeight: '100px' }}
                  placeholder="Add details, acceptance criteria, etc..."
                  value={newTaskData.description}
                  onChange={(e) => setNewTaskData({ ...newTaskData, description: e.target.value })}
                />
              </div>
              <div className="task-form-grid">
                <div className="task-form-group">
                  <label className="task-form-label">Priority</label>
                  <select
                    className="task-form-select"
                    value={newTaskData.priority}
                    onChange={(e) => setNewTaskData({ ...newTaskData, priority: e.target.value })}
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
                    onChange={(e) => setNewTaskData({ ...newTaskData, issue_type: e.target.value })}
                  >
                    <option value="task">Task</option>
                    <option value="bug">Bug</option>
                    <option value="story">Story</option>
                  </select>
                </div>
              </div>
              {/* Task Scoring Section */}
              <div className="task-form-grid">
                <div className="task-form-group">
                  <label className="task-form-label">Impact</label>
                  <select
                    className="task-form-select"
                    value={newTaskData.impact !== undefined ? newTaskData.impact : 5}
                    onChange={(e) => setNewTaskData({ ...newTaskData, impact: parseInt(e.target.value) })}
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
                    value={newTaskData.risk || 'medium'}
                    onChange={(e) => setNewTaskData({ ...newTaskData, risk: e.target.value })}
                  >
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>
              </div>
              <div className="task-form-group">
                <label className="task-form-label">Linked Goal</label>
                <select
                  className="task-form-select"
                  value={newTaskData.goal || ''}
                  onChange={(e) => setNewTaskData({ ...newTaskData, goal: e.target.value || '' })}
                >
                  <option value="">No Goal Linked</option>
                  {goals.map(g => (
                    <option key={g.id} value={g.id}>{g.title}</option>
                  ))}
                </select>
              </div>
              <div className="task-form-group">
                <label className="task-form-label">Assignment</label>
                {/* Commented: Smart Suggestion Feature
                          <div style={{ display: 'flex', border: '1px solid #cbd5e1', borderRadius: '8px', overflow: 'hidden', width: 'fit-content' }}>
                            <button
                              type="button"
                              onClick={() => setCreateAssignMode('manual')}
                              style={{
                                padding: '0.4rem 1rem',
                                fontSize: '0.8rem',
                                border: 'none',
                                background: createAssignMode === 'manual' ? '#6366f1' : 'white',
                                color: createAssignMode === 'manual' ? 'white' : '#475569',
                                fontWeight: 500,
                                cursor: 'pointer',
                                transition: 'all 0.2s'
                              }}
                            >
                              Manual Assign
                            </button>
                            <button
                              type="button"
                              onClick={async () => {
                                setCreateAssignMode('suggest');
                                setCreateSmartSuggestLoading(true);
                                setCreateSmartSuggestError(null);
                                try {
                                  const params = {
                                    estimated_hours: newTaskData.estimated_hours || 1.0,
                                    priority: newTaskData.priority || 'medium',
                                    impact: newTaskData.impact !== undefined ? newTaskData.impact : 5,
                                    risk: newTaskData.risk || 'medium'
                                  };
                                  const response = await getSmartSuggest(selectedOrg.id, params);
                                  setCreateSmartSuggestions(response.suggestions || []);
                                } catch (err) {
                                  console.error(err);
                                  setCreateSmartSuggestError("Failed to fetch suggestions.");
                                } finally {
                                  setCreateSmartSuggestLoading(false);
                                }
                              }}
                              style={{
                                padding: '0.4rem 1rem',
                                fontSize: '0.8rem',
                                border: 'none',
                                background: createAssignMode === 'suggest' ? '#6366f1' : 'white',
                                color: createAssignMode === 'suggest' ? 'white' : '#475569',
                                fontWeight: 500,
                                cursor: 'pointer',
                                transition: 'all 0.2s'
                              }}
                            >
                              Smart Suggest
                            </button>
                          </div>
                          */}
                          { createAssignMode === 'manual' ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                        <select
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
                            const name = m.user?.first_name || m.user?.last_name ? `${m.user.first_name || ''} ${m.user.last_name || ''}`.trim() : m.email;
                            return (
                              <option key={userId} value={userId}>
                                {name}
                              </option>
                            );
                          })}
                        </select>
                        <div style={{ display: 'flex', gap: '1rem', marginTop: '0.75rem' }}>
                          <div className="task-form-group" style={{ flex: 1, marginBottom: 0 }}>
                            <label className="task-form-label">Estimated Hours</label>
                            <input
                              type="number"
                              min="0"
                              className="task-form-input"
                              placeholder="e.g. 2"
                              value={newTaskData.estimated_hours_part || ''}
                              onChange={(e) => {
                                const h = e.target.value;
                                const m = newTaskData.estimated_minutes_part || '0';
                                const totalMins = (parseInt(h || '0') * 60) + parseInt(m || '0');
                                setNewTaskData(prev => ({ ...prev, estimated_hours_part: h, estimated_minutes: totalMins.toString(), estimated_hours: (totalMins / 60.0).toFixed(2) }));
                              }}
                            />
                          </div>
                          <div className="task-form-group" style={{ flex: 1, marginBottom: 0 }}>
                            <label className="task-form-label">Estimated Minutes</label>
                            <input
                              type="number"
                              min="0"
                              max="59"
                              className="task-form-input"
                              placeholder="e.g. 30"
                              value={newTaskData.estimated_minutes_part || ''}
                              onChange={(e) => {
                                const m = e.target.value;
                                const h = newTaskData.estimated_hours_part || '0';
                                const totalMins = (parseInt(h || '0') * 60) + parseInt(m || '0');
                                setNewTaskData(prev => ({ ...prev, estimated_minutes_part: m, estimated_minutes: totalMins.toString(), estimated_hours: (totalMins / 60.0).toFixed(2) }));
                              }}
                            />
                          </div>
                        </div>

                        {/* Schedule Preview Section */}
                        {(newTaskData.assignees && newTaskData.assignees.length > 0 && parseInt(newTaskData.estimated_minutes || '0') > 0) && (
                          <div style={{ padding: '1rem', background: schedulePreview.isLoading ? '#f8fafc' : (scheduledTime.startDate ? '#f0fdf4' : '#fffbeb'), borderRadius: '8px', border: '1px solid', borderColor: schedulePreview.isLoading ? '#e2e8f0' : (scheduledTime.startDate ? '#bbf7d0' : '#fde68a'), marginTop: '1rem' }}>
                            <h5 style={{ margin: '0 0 0.5rem 0', fontSize: '0.85rem', color: '#1e293b', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              <Calendar size={14} /> Schedule Preview
                            </h5>
                            <div style={{ fontSize: '0.75rem', color: '#475569', marginBottom: '0.75rem', paddingBottom: '0.5rem', borderBottom: '1px dashed #cbd5e1' }}>
                              Assignee Working Hours: <strong>{activeTaskAssigneeSchedule ? `${(activeTaskAssigneeSchedule.work_start_time || '10:00:00').substring(0,5)} to ${(activeTaskAssigneeSchedule.work_end_time || '19:00:00').substring(0,5)}` : 'Default (10:00 to 19:00)'}</strong>
                            </div>
                            {schedulePreview.isLoading ? (
                              <div style={{ fontSize: '0.8rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <div style={{ width: '12px', height: '12px', borderRadius: '50%', border: '2px solid #cbd5e1', borderTopColor: '#6366f1', animation: 'spin 1s linear infinite' }} />
                                Calculating optimal schedule...
                              </div>
                            ) : scheduledTime.startDate ? (() => {
                              const formatDateString = (dateStr) => {
                                if (!dateStr) return '';
                                const parts = dateStr.split('-');
                                if (parts.length !== 3) return dateStr;
                                const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                                return `${parseInt(parts[2], 10)} ${months[parseInt(parts[1], 10) - 1]} ${parts[0]}`;
                              };
                              const formatTimeString = (timeStr) => {
                                if (!timeStr) return '';
                                const parts = timeStr.split(':');
                                const hour = parseInt(parts[0], 10);
                                const min = parseInt(parts[1], 10);
                                if (isNaN(hour) || isNaN(min)) return timeStr;
                                const ampm = hour >= 12 ? 'PM' : 'AM';
                                const displayHour = hour % 12 || 12;
                                const displayMin = min < 10 ? `0${min}` : min;
                                return `${displayHour}:${displayMin} ${ampm}`;
                              };
                              return (
                                <div>
                                  <div style={{ fontSize: '0.8rem', color: '#166534', fontWeight: 600, marginBottom: '0.25rem' }}>✓ Slot Available</div>
                                  <div style={{ fontSize: '0.8rem', color: '#475569', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                      <span>Starts:</span>
                                      <strong>{formatDateString(scheduledTime.startDate)} at {formatTimeString(scheduledTime.startTime)}</strong>
                                    </div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                      <span>Ends:</span>
                                      <strong>{formatDateString(scheduledTime.endDate)} at {formatTimeString(scheduledTime.endTime)}</strong>
                                    </div>
                                  </div>
                                </div>
                              );
                            })()
                            : (
                              <div>
                                <div style={{ fontSize: '0.8rem', color: '#b45309', fontWeight: 600, marginBottom: '0.25rem' }}>⚠ Task will go to Queue Bucket</div>
                                <div style={{ fontSize: '0.75rem', color: '#92400e' }}>
                                  {schedulePreview.message || "No continuous free slot available within the scan period."}
                                </div>
                              </div>
                            )}
                          </div>
                        )}

                        {/* Member Past Stats */}
                        {(() => {
                          const selectedId = newTaskData.assignees && newTaskData.assignees[0];
                          if (!selectedId) return null;
                          const stats = getMemberStats(selectedId);
                          if (!stats) return null;
                          return (
                            <div style={{ fontSize: '0.78rem', color: '#475569', background: '#f8fafc', padding: '0.4rem 0.6rem', borderRadius: '6px', border: '1px solid #cbd5e1', marginTop: '0.75rem' }}>
                              📈 <strong>Past Performance:</strong> {stats.performance}% | ⚡ <strong>Efficiency:</strong> {stats.efficiency}x | 💼 Completed {stats.completed} similar tasks
                            </div>
                          );
                        })()}
                      </div>
                    ) : (
                      /* Commented: Smart Suggestion Feature */
                      false && (
                        <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                          {createSmartSuggestLoading ? (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: '#64748b' }}>
                              <div style={{ border: '2px solid #f3f3f3', borderTop: '2px solid #6366f1', borderRadius: '50%', width: '16px', height: '16px', animation: 'spin 1s linear infinite' }} />
                              <span>Analyzing candidate match scores...</span>
                            </div>
                          ) : createSmartSuggestError ? (
                            <span style={{ fontSize: '0.8rem', color: '#ef4444' }}>{createSmartSuggestError}</span>
                          ) : createSmartSuggestions.length === 0 ? (
                            <span style={{ fontSize: '0.8rem', color: '#64748b', fontStyle: 'italic' }}>No members available to suggest</span>
                          ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                              {/* Featured Recommendation Box */}
                              {(() => {
                                const topSugg = createSmartSuggestions[0];
                                const stats = getMemberStats(topSugg.id);
                                const isAssigned = newTaskData.assignees && newTaskData.assignees[0] === topSugg.id;
                                const isNewMember = (topSugg.reason || '').includes('New member');
                                return (
                                  <div style={{ background: '#f5f7ff', border: '1px solid #c7d2fe', borderRadius: '10px', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '0.75rem' }}>
                                    <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#4f46e5', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                      🌟 Recommended: {topSugg.email || topSugg.name}
                                    </div>
                                    <div style={{ fontSize: '0.78rem', fontWeight: 600, color: '#4f46e5' }}>
                                      Match Score: {Math.round(topSugg.match_score)} (Higher is better)
                                    </div>
                                    {topSugg.email && topSugg.name && (
                                      <div style={{ fontSize: '0.74rem', color: '#6366f1', opacity: 0.8, marginTop: '-0.25rem' }}>✉ {topSugg.email}</div>
                                    )}
                                    <div style={{ fontSize: '0.78rem', color: '#475569' }}>
                                      <strong>Reason:</strong> {topSugg.reason}
                                    </div>
                                    {stats && (
                                      <div style={{ fontSize: '0.74rem', color: '#64748b' }}>
                                        Past Performance: {isNewMember ? '70% (new member baseline)' : `${stats.performance}%`} | Efficiency: {stats.efficiency}x
                                      </div>
                                    )}
                                    <button
                                      type="button"
                                      disabled={isAssigned}
                                      onClick={() => {
                                        setNewTaskData(prev => ({
                                          ...prev,
                                          assignees: [topSugg.id]
                                        }));
                                      }}
                                      style={{
                                        width: 'fit-content',
                                        padding: '0.35rem 0.85rem',
                                        fontSize: '0.75rem',
                                        marginTop: '0.25rem',
                                        background: isAssigned ? '#10b981' : '#6366f1',
                                        borderColor: 'transparent',
                                        color: 'white',
                                        borderRadius: '6px',
                                        fontWeight: 500,
                                        cursor: isAssigned ? 'default' : 'pointer'
                                      }}
                                    >
                                      {isAssigned ? '✓ Assigned to Recommended' : 'Assign to Recommended'}
                                    </button>
                                  </div>
                                );
                              })()}
                              {/* List of suggestions */}
                              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginTop: '0.5rem' }}>All Suggestions:</div>
                              {createSmartSuggestions.map((sugg, idx) => {
                                const isSelected = newTaskData.assignees && newTaskData.assignees[0] === sugg.id;
                                const stats = getMemberStats(sugg.id);
                                const isNewMember = (sugg.reason || '').includes('New member');
                                return (
                                  <div
                                    key={sugg.id}
                                    style={{
                                      display: 'flex',
                                      alignItems: 'center',
                                      justifyContent: 'space-between',
                                      padding: '0.75rem',
                                      background: isSelected ? '#f5f7ff' : 'white',
                                      border: isSelected ? '1px solid #6366f1' : '1px solid #e2e8f0',
                                      borderRadius: '6px',
                                      gap: '1rem'
                                    }}
                                  >
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
                                        <span style={{ fontWeight: 700, fontSize: '0.82rem', color: '#1e293b' }}>{sugg.name || sugg.email}</span>
                                        {sugg.is_busy ? (
                                          <span style={{ background: '#fee2e2', color: '#b91c1c', border: '1px solid #fca5a5', fontSize: '0.6rem', padding: '0.05rem 0.25rem', borderRadius: '4px', fontWeight: 600 }}>BUSY</span>
                                        ) : (
                                          <span style={{ background: '#ecfdf5', color: '#047857', border: '1px solid #6ee7b7', fontSize: '0.6rem', padding: '0.05rem 0.25rem', borderRadius: '4px', fontWeight: 600 }}>FREE</span>
                                        )}
                                      </div>
                                      {sugg.email && sugg.name && (
                                        <span style={{ fontSize: '0.71rem', color: '#94a3b8' }}>✉ {sugg.email}</span>
                                      )}
                                      <span style={{ fontSize: '0.74rem', color: '#475569', display: 'flex', alignItems: 'center', gap: '0.2rem', flexWrap: 'wrap' }}>
                                        <Award size={11} style={{ color: '#fbbf24' }} /> Match Score: <strong>{sugg.match_score}</strong>
                                        {stats && (
                                          <>
                                            <span style={{ color: '#cbd5e1' }}>|</span>
                                            <span>Perf: {isNewMember ? '70% baseline' : `${stats.performance}%`}</span>
                                          </>
                                        )}
                                        <span style={{ color: '#cbd5e1' }}>|</span>
                                        <span style={{ fontStyle: 'italic', color: '#64748b' }}>{sugg.reason}</span>
                                      </span>
                                      {null}
                                    </div>
                                    <button
                                      type="button"
                                      onClick={() => {
                                        setNewTaskData(prev => ({
                                          ...prev,
                                          assignees: [sugg.id]
                                        }));
                                      }}
                                      className={isSelected ? "btn-secondary" : "btn-primary"}
                                      style={{
                                        padding: '0.35rem 0.75rem',
                                        fontSize: '0.75rem',
                                        width: 'auto',
                                        borderRadius: '6px',
                                        borderColor: isSelected ? '#6366f1' : 'transparent',
                                        background: isSelected ? 'white' : '#6366f1',
                                        color: isSelected ? '#6366f1' : 'white'
                                      }}
                                    >
                                      {isSelected ? 'Assigned' : 'Use'}
                                    </button>
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      )
                    )}
              </div>
              <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                <div className="task-form-group" style={{ flex: 1, marginBottom: 0 }}>
                  <label className="task-form-label">Due Date</label>
                  <input
                    type="date"
                    className="task-form-input"
                    value={newTaskData.due_date || ''}
                    onChange={(e) => setNewTaskData(prev => ({ ...prev, due_date: e.target.value }))}
                  />
                </div>
                <div className="task-form-group" style={{ flex: 1, marginBottom: 0 }}>
                  <label className="task-form-label">Status</label>
                  <select
                    className="task-form-select"
                    value={newTaskData.status || 'todo'}
                    onChange={(e) => setNewTaskData(prev => ({ ...prev, status: e.target.value }))}
                  >
                    <option value="todo">To Do</option>
                    <option value="in_progress">In Progress</option>
                    <option value="review">Review</option>
                    <option value="done">Done</option>
                  </select>
                </div>
              </div>
              <div className="task-form-group" style={{ marginTop: '1rem' }}>
                <label className="task-form-label">Sharing & Permissions</label>
                <button
                  type="button"
                  onClick={() => openSharingModal('newTaskData', newTaskData)}
                  style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem', background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '8px', cursor: 'pointer', color: '#334155', fontWeight: 500, justifyContent: 'space-between', width: '100%', outline: 'none' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Users size={16} style={{ color: '#6366f1' }} />
                    <span>
                      {newTaskData.sharing_option === 'private' ? 'Private' : newTaskData.sharing_option === 'specific' ? 'Specific People' : 'Entire Workspace'}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: '#94a3b8', marginLeft: '0.5rem' }}>
                      ({newTaskData.assignees?.length || 0} Assignees
                      {newTaskData.sharing_option === 'specific' ? `, ${newTaskData.shared_viewers?.length || 0} Viewers` : ''})
                    </span>
                  </div>
                </button>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem', paddingTop: '1.25rem', borderTop: '1px solid #f1f5f9' }}>
                <button type="button" onClick={() => setTasksView('list')} className="btn-secondary" style={{ width: 'auto', padding: '0.6rem 1.2rem' }}>Cancel</button>
                <button type="submit" disabled={loading} className="btn-primary" style={{ width: 'auto', padding: '0.6rem 1.5rem' }}>{loading ? 'Creating...' : 'Create Task'}</button>
              </div>
            </form>
          </div>
        </div>
        );
}
if (tasksView === 'detail' && activeTask) {
  const isEditable = canEditTask(activeTask);
  const currentUserEmail = sessionStorage.getItem('email');
  const currentUserId = sessionStorage.getItem('userId');
  const isAssignee = (Array.isArray(activeTask?.assignees) && activeTask.assignees.some(a => {
    if (typeof a === 'object' && a !== null) {
      return a.email === currentUserEmail || String(a.id) === String(currentUserId);
    }
    return String(a) === String(currentUserId);
  })) || (Array.isArray(activeTask?.assignee_details) && activeTask.assignee_details.some(d => d.email === currentUserEmail || String(d.id) === String(currentUserId)));
  const isCreator = activeTask?.created_by_details?.email === currentUserEmail || String(activeTask?.created_by) === String(currentUserId);
  const isStatusEditable = isEditable || isAssignee || isCreator;
  return (
    <div className="task-detail-layout">
      {/* Left Column: Main Task Content */}
      <div className="task-detail-main">
        <button
          onClick={() => setTasksView('list')}
          className="back-btn-premium"
          style={{ marginBottom: '1.5rem' }}
        >
          <ArrowLeft size={16} /> Back to Tasks
        </button>
        {!isEditable && (
          <div style={{ padding: '0.75rem 1rem', backgroundColor: (isAssignee || isCreator) ? '#eef2ff' : '#fffbeb', border: `1px solid ${(isAssignee || isCreator) ? '#e0e7ff' : '#fef3c7'}`, borderRadius: '12px', color: (isAssignee || isCreator) ? '#4f46e5' : '#b45309', fontSize: '0.85rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertCircle size={16} />
            <span>
              {(isAssignee || isCreator)
                ? "You are assigned to or created this task. You can change its status, but other details are read-only."
                : 'You have read-only access to this task. Grant "Edit & Update Tasks" permission to modify.'}
            </span>
          </div>
        )}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <span className="member-role-badge-premium role-medium" style={{ textTransform: 'uppercase', fontSize: '0.65rem' }}>{activeTask.issue_type}</span>
          <span style={{ color: '#cbd5e1' }}>•</span>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8' }}>
            Created by {activeTask.created_by_details?.first_name || activeTask.created_by_details?.email}
          </span>
        </div>
        <input
          type="text"
          value={activeTask.title || ''}
          onChange={(e) => {
            if (!isEditable) return;
            setActiveTask({ ...activeTask, title: e.target.value });
          }}
          onBlur={async (e) => {
            if (!isEditable) return;
            if (!e.target.value.trim()) return;
            try {
              const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { title: e.target.value });
              setActiveTask(updated);
              handleLoadTasks();
            } catch (err) {
              console.error(err);
            }
          }}
          readOnly={!isEditable}
          style={{ cursor: isEditable ? 'pointer' : 'not-allowed' }}
          className="editable-task-title-input"
          placeholder="Task Title"
        />
        <textarea
          value={activeTask.description || ''}
          onChange={(e) => {
            if (!isEditable) return;
            setActiveTask({ ...activeTask, description: e.target.value });
          }}
          onBlur={async (e) => {
            if (!isEditable) return;
            try {
              const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { description: e.target.value });
              setActiveTask(updated);
              handleLoadTasks();
            } catch (err) {
              console.error(err);
            }
          }}
          readOnly={!isEditable}
          style={{
            fontSize: '0.925rem',
            color: '#475569',
            lineHeight: 1.6,
            width: '100%',
            minHeight: '120px',
            border: '1px solid transparent',
            background: 'transparent',
            resize: 'vertical',
            outline: 'none',
            padding: '0.5rem',
            borderRadius: '8px',
            marginBottom: '2rem',
            fontFamily: 'inherit',
            cursor: isEditable ? 'text' : 'not-allowed'
          }}
          onFocus={(e) => {
            if (!isEditable) return;
            e.target.style.border = '1px solid #e2e8f0';
            e.target.style.background = '#f8fafc';
          }}
          placeholder="Add a detailed description..."
        />
        {/* Comments Section */}
        <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '2rem', marginTop: '2rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#0f172a', margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <MessageSquare size={18} style={{ color: '#6366f1' }} /> Comments & Discussion
          </h3>
          {/* New Comment/Reply Input Form */}
          <form onSubmit={handleCommentSubmit} style={{ marginBottom: '2rem' }}>
            {replyToCommentId && (
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#eef2ff', border: '1px solid #e0e7ff', padding: '0.5rem 0.75rem', borderRadius: '8px', marginBottom: '0.5rem', fontSize: '0.8rem', color: '#4f46e5' }}>
                <span>Replying to thread...</span>
                <button type="button" onClick={() => setReplyToCommentId(null)} style={{ border: 'none', background: 'none', color: '#ef4444', fontWeight: 'bold', cursor: 'pointer' }}>Cancel</button>
              </div>
            )}
            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
              <textarea
                value={newCommentText}
                onChange={(e) => setNewCommentText(e.target.value)}
                placeholder={replyToCommentId ? "Write a reply..." : "Write a comment... (Tip: @mention team members)"}
                style={{
                  flex: 1,
                  minHeight: '80px',
                  padding: '0.75rem 1rem',
                  borderRadius: '12px',
                  border: '1px solid #cbd5e1',
                  fontSize: '0.875rem',
                  outline: 'none',
                  resize: 'vertical',
                  fontFamily: 'inherit',
                  background: '#fff',
                  boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.05)'
                }}
              />
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
              <button
                type="submit"
                style={{
                  backgroundColor: '#6366f1',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '0.5rem 1.25rem',
                  fontSize: '0.875rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s',
                  boxShadow: '0 1px 3px rgba(99, 102, 241, 0.4)'
                }}
                onMouseEnter={(e) => e.target.style.backgroundColor = '#4f46e5'}
                onMouseLeave={(e) => e.target.style.backgroundColor = '#6366f1'}
              >
                {replyToCommentId ? 'Post Reply' : 'Post Comment'}
              </button>
            </div>
          </form>
          {/* Threaded comments list */}
          <div className="task-comments-container" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {comments.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '2rem 1rem', color: '#94a3b8', fontSize: '0.875rem', backgroundColor: '#f8fafc', borderRadius: '12px', border: '1px dashed #e2e8f0' }}>
                No comments yet. Start the conversation!
              </div>
            ) : (
              renderCommentTree(comments)
            )}
          </div>
        </div>
      </div>
      {/* Resize Handle */}
      <div
        onMouseDown={handleTaskSidebarResize}
        style={{
          width: '6px',
          cursor: 'col-resize',
          alignSelf: 'stretch',
          background: '#e2e8f0',
          margin: '0 -3px',
          zIndex: 10,
          transition: 'background 0.2s',
          borderRadius: '3px',
          flexShrink: 0
        }}
        onMouseEnter={(e) => e.target.style.background = '#6366f1'}
        onMouseLeave={(e) => e.target.style.background = '#e2e8f0'}
      />
      {/* Right Column: Task Metadata Sidebar */}
      <div className="task-detail-sidebar" style={{ width: `${taskSidebarWidth}px`, flexShrink: 0 }}>
        <div className="task-detail-meta-group">
          <h4 className="task-detail-meta-label">Status</h4>
          <select
            className="task-form-select"
            style={{ padding: '0.6rem 0.8rem', background: 'white' }}
            value={activeTask.status}
            disabled={!isStatusEditable}
            onChange={async (e) => {
              try {
                const newStatus = e.target.value;
                const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { status: newStatus });
                setActiveTask(updated);
                handleLoadTasks();
                if (newStatus === 'done') {
                  setFeedbackModalConfig({ isOpen: true, taskId: updated.id, taskTitle: updated.title });
                }
              } catch (err) {
                console.error(err);
                const errMsg = err.response?.data?.error ||
                  err.response?.data?.detail ||
                  (err.response?.data?.status ? (Array.isArray(err.response.data.status) ? err.response.data.status[0] : err.response.data.status) : null) ||
                  'Failed to update task status.';
                if (errMsg.includes('already has another task In Progress') || errMsg.includes('already has another task') || errMsg.includes('already has another task in progress')) {
                  setWorkloadLimitWarning(errMsg);
                } else {
                  setError(errMsg);
                }
              }
            }}
          >
            <option value="backlog">Backlog</option>
            <option value="todo">To Do</option>
            <option value="in_progress">In Progress</option>
            <option value="in_review">In Review</option>
            <option value="testing">Testing</option>
            <option value="done">Done</option>
          </select>
        </div>
        {activeTask.tickets && activeTask.tickets.length > 0 && (
          <div className="task-detail-meta-group">
            <h4 className="task-detail-meta-label">Assignee Tickets</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', background: '#f8fafc', padding: '0.75rem', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
              {activeTask.tickets.map(ticket => {
                const currentUserEmail = sessionStorage.getItem('email');
                const currentUserId = sessionStorage.getItem('userId');
                const isMyTicket = ticket.assignee_email === currentUserEmail || String(ticket.assignee) === String(currentUserId);
                const isUserAdminOrOwner = selectedOrg?.my_status?.role === 'owner' || selectedOrg?.my_status?.role === 'admin';
                const canModifyThisTicket = isMyTicket || isUserAdminOrOwner;
                return (
                  <div key={ticket.id} style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem' }}>
                      <span style={{ fontWeight: 600, color: '#334155' }}>
                        {ticket.assignee_name} {isMyTicket && <span style={{ color: '#6366f1', fontSize: '0.7rem', fontWeight: 'normal' }}>(You)</span>}
                      </span>
                    </div>
                    {canModifyThisTicket ? (
                      <select
                        className="task-form-select"
                        style={{ padding: '0.35rem 0.5rem', background: 'white', fontSize: '0.75rem', marginTop: '0.15rem' }}
                        value={ticket.status}
                        onChange={async (e) => {
                          try {
                            const updatedTicket = await handleUpdateTicketStatus(ticket.id, e.target.value);
                            // Update local state for immediate feedback
                            const updatedTickets = activeTask.tickets.map(t => t.id === ticket.id ? { ...t, ...updatedTicket } : t);
                            setActiveTask({ ...activeTask, tickets: updatedTickets });
                            // Refetch full task details to stay perfectly synced with backend changes
                            const updatedTask = await getOrgTaskDetail(selectedOrg.slug, activeTask.id);
                            setActiveTask(updatedTask);
                            handleLoadTasks();
                          } catch (err) {
                            console.error(err);
                          }
                        }}
                      >
                        <option value="backlog">Backlog</option>
                        <option value="todo">To Do</option>
                        <option value="in_progress">In Progress</option>
                        <option value="in_review">In Review</option>
                        <option value="testing">Testing</option>
                        <option value="done">Done</option>
                      </select>
                    ) : (
                      <span className={`member-role-badge-premium status-${ticket.status}`} style={{ fontSize: '0.68rem', padding: '0.15rem 0.4rem', alignSelf: 'start', marginTop: '0.15rem' }}>
                        {ticket.status.replace('_', ' ').toUpperCase()}
                      </span>
                    )}
                    <TicketTimer
                      ticket={ticket}
                      totalEstimatedMinutes={activeTask.estimated_minutes}
                      numAssignees={activeTask.tickets.length}
                    />
                  </div>
                );
              })}
            </div>
          </div>
        )}
        <div className="task-detail-meta-group">
          <h4 className="task-detail-meta-label">Priority</h4>
          <select
            className="task-form-select"
            style={{ padding: '0.6rem 0.8rem', background: 'white' }}
            value={activeTask.priority}
            disabled={!isEditable}
            onChange={async (e) => {
              try {
                const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { priority: e.target.value });
                setActiveTask(updated);
                handleLoadTasks();
              } catch (err) {
                console.error(err);
              }
            }}
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>
        <div className="task-detail-meta-group">
          <h4 className="task-detail-meta-label">Linked Goal</h4>
          <select
            className="task-form-select"
            style={{ padding: '0.6rem 0.8rem', background: 'white' }}
            value={activeTask.goal || ''}
            disabled={!isEditable}
            onChange={async (e) => {
              try {
                const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { goal: e.target.value || null });
                setActiveTask(updated);
                handleLoadTasks();
              } catch (err) {
                console.error(err);
              }
            }}
          >
            <option value="">No Goal Linked</option>
            {goals.map(g => (
              <option key={g.id} value={g.id}>{g.title}</option>
            ))}
          </select>
        </div>
        <div className="task-detail-meta-group">
          <h4 className="task-detail-meta-label">Start Date</h4>
          <input
            type="date"
            className="task-form-input"
            style={{ padding: '0.6rem 0.8rem', background: 'white' }}
            value={activeTask.start_date ? activeTask.start_date.substring(0, 10) : ''}
            disabled={!isEditable}
            onChange={async (e) => {
              try {
                const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { start_date: e.target.value || null });
                setActiveTask(updated);
                handleLoadTasks();
              } catch (err) {
                console.error(err);
              }
            }}
          />
        </div>
        <div className="task-detail-meta-group">
          <h4 className="task-detail-meta-label">Due Date (End Time)</h4>
          <input
            type="datetime-local"
            className="task-form-input"
            style={{ padding: '0.6rem 0.8rem', background: 'white' }}
            value={(() => {
              if (!activeTask.due_date) return '';
              const date = new Date(activeTask.due_date);
              const pad = (num) => String(num).padStart(2, '0');
              const yyyy = date.getFullYear();
              const mm = pad(date.getMonth() + 1);
              const dd = pad(date.getDate());
              const hh = pad(date.getHours());
              const min = pad(date.getMinutes());
              return `${yyyy}-${mm}-${dd}T${hh}:${min}`;
            })()}
            disabled={!isEditable}
            onChange={async (e) => {
              try {
                const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { due_date: e.target.value || null });
                setActiveTask(updated);
                handleLoadTasks();
              } catch (err) {
                console.error(err);
              }
            }}
          />
        </div>
        {/* Time & Planning Section */}
        <div className="task-detail-meta-group" style={{ borderTop: '1px solid #f1f5f9', paddingTop: '1.25rem', marginTop: '1.25rem' }}>
          <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#475569', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Time & Planning</h4>
          {/* Estimated Time */}
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600 }}>Est. Hours</label>
              <input
                type="number"
                step="0.1"
                min="0"
                placeholder="0.0"
                className="task-form-input"
                style={{ padding: '0.4rem 0.6rem', background: 'white' }}
                value={activeTask.estimated_hours || ''}
                disabled={!isEditable}
                onChange={async (e) => {
                  const val = e.target.value === '' ? null : parseFloat(e.target.value);
                  setActiveTask({ ...activeTask, estimated_hours: val });
                }}
                onBlur={async (e) => {
                  try {
                    const val = e.target.value === '' ? null : parseFloat(e.target.value);
                    const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { estimated_hours: val });
                    setActiveTask(updated);
                    handleLoadTasks();
                  } catch (err) {
                    console.error(err);
                  }
                }}
              />
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600 }}>Est. Minutes</label>
              <input
                type="number"
                min="0"
                placeholder="0"
                className="task-form-input"
                style={{ padding: '0.4rem 0.6rem', background: 'white' }}
                value={activeTask.estimated_minutes || ''}
                disabled={!isEditable}
                onChange={async (e) => {
                  const val = e.target.value === '' ? null : parseInt(e.target.value, 10);
                  setActiveTask({ ...activeTask, estimated_minutes: val });
                }}
                onBlur={async (e) => {
                  try {
                    const val = e.target.value === '' ? null : parseInt(e.target.value, 10);
                    const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { estimated_minutes: val });
                    setActiveTask(updated);
                    handleLoadTasks();
                  } catch (err) {
                    console.error(err);
                  }
                }}
              />
            </div>
          </div>
          {/* Actual Time Spent */}
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600 }}>
                Actual Hours {activeTask.tickets && activeTask.tickets.length > 0 && '(Auto)'}
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                placeholder="0.0"
                className="task-form-input"
                style={{ padding: '0.4rem 0.6rem', background: activeTask.tickets && activeTask.tickets.length > 0 ? '#f1f5f9' : 'white' }}
                value={activeTask.tickets && activeTask.tickets.length > 0 ? (liveActualMins / 60).toFixed(2) : (activeTask.actual_hours || '')}
                disabled={!isEditable || (activeTask.tickets && activeTask.tickets.length > 0)}
                onChange={async (e) => {
                  const val = e.target.value === '' ? null : parseFloat(e.target.value);
                  setActiveTask({ ...activeTask, actual_hours: val });
                }}
                onBlur={async (e) => {
                  try {
                    const val = e.target.value === '' ? null : parseFloat(e.target.value);
                    const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { actual_hours: val });
                    setActiveTask(updated);
                    handleLoadTasks();
                  } catch (err) {
                    console.error(err);
                  }
                }}
              />
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600 }}>
                Actual Mins {activeTask.tickets && activeTask.tickets.length > 0 && '(Auto)'}
              </label>
              <input
                type="number"
                min="0"
                placeholder="0"
                className="task-form-input"
                style={{ padding: '0.4rem 0.6rem', background: activeTask.tickets && activeTask.tickets.length > 0 ? '#f1f5f9' : 'white' }}
                value={activeTask.tickets && activeTask.tickets.length > 0 ? Math.floor(liveActualMins) : (activeTask.actual_time_spent_minutes || '')}
                disabled={!isEditable || (activeTask.tickets && activeTask.tickets.length > 0)}
                onChange={async (e) => {
                  const val = e.target.value === '' ? null : parseInt(e.target.value, 10);
                  setActiveTask({ ...activeTask, actual_time_spent_minutes: val });
                }}
                onBlur={async (e) => {
                  try {
                    const val = e.target.value === '' ? null : parseInt(e.target.value, 10);
                    const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { actual_time_spent_minutes: val });
                    setActiveTask(updated);
                    handleLoadTasks();
                  } catch (err) {
                    console.error(err);
                  }
                }}
              />
            </div>
          </div>
          {/* Computed Planning Metrics */}
          <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '0.75rem', marginTop: '0.75rem' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#334155', marginBottom: '0.4rem' }}>Workday Calculations</div>
            {/* Days Needed */}
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#475569', marginBottom: '0.25rem' }}>
              <span>Days Needed:</span>
              <span style={{ fontWeight: 600 }}>{activeTask.days_needed ? `${activeTask.days_needed} days` : '0 days'}</span>
            </div>
            {/* Intelligent Schedule Status & Times */}
            <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: '0.5rem', marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#475569' }}>
                <span>Schedule Status:</span>
                <span style={{
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  fontSize: '0.7rem',
                  padding: '0.1rem 0.35rem',
                  borderRadius: '4px',
                  background: activeTask.schedule_status === 'SCHEDULED' ? '#ecfdf5' : activeTask.schedule_status === 'COMPLETED' ? '#eff6ff' : '#fffbeb',
                  color: activeTask.schedule_status === 'SCHEDULED' ? '#047857' : activeTask.schedule_status === 'COMPLETED' ? '#1d4ed8' : '#b45309'
                }}>
                  {activeTask.schedule_status || 'QUEUED'}
                </span>
              </div>
              {activeTask.planned_start && (
                <div style={{ fontSize: '0.72rem', color: '#64748b', paddingLeft: '0.25rem' }}>
                  <div>Start: <strong style={{ color: '#334155' }}>{new Date(activeTask.planned_start).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}</strong></div>
                  <div>End: <strong style={{ color: '#334155' }}>{new Date(activeTask.planned_end).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}</strong></div>
                  
                  {activeTask.segments && activeTask.segments.length > 0 && (
                    <div style={{ marginTop: '0.5rem', background: '#fff', border: '1px solid #e2e8f0', borderRadius: '6px', padding: '0.5rem' }}>
                      <div style={{ fontWeight: 600, color: '#475569', marginBottom: '0.35rem' }}>Allocated Segments:</div>
                      {activeTask.segments.map((seg, idx) => (
                        <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem', padding: '0.35rem', borderBottom: idx < activeTask.segments.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ fontWeight: 600, color: '#334155' }}>Segment {idx + 1}</span>
                            <span style={{ color: '#0ea5e9', fontWeight: 600 }}>
                              {seg.duration >= 60 
                                ? `${Math.floor(seg.duration / 60)}h ${seg.duration % 60}m` 
                                : `${seg.duration}m`}
                            </span>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b', fontSize: '0.65rem' }}>
                            <span>{new Date(seg.start).toLocaleDateString([], { month: 'short', day: 'numeric' })}</span>
                            <span>{new Date(seg.start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })} &rarr; {new Date(seg.end).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
            {/* Load Warnings */}
            {activeTask.load_warnings && activeTask.load_warnings.length > 0 && (
              <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                {activeTask.load_warnings.map((w, idx) => (
                  <div key={idx} style={{ display: 'flex', gap: '0.25rem', alignItems: 'flex-start', fontSize: '0.7rem', color: '#b91c1c', background: '#fef2f2', padding: '0.35rem', borderRadius: '4px', border: '1px solid #fee2e2' }}>
                    <AlertCircle size={12} style={{ flexShrink: 0, marginTop: '1px' }} />
                    <span>{w.message}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
        <div className="task-detail-meta-group">
          <h4 className="task-detail-meta-label" style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <Users size={14} /> Assignees
          </h4>
          <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem', boxShadow: '0 1px 2px rgba(0,0,0,0.02)' }}>
            {activeTask.assignee_details?.length > 0 ? (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', marginBottom: '0.5rem' }}>
                {activeTask.assignee_details.map(u => (
                  <div key={u.id} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem', color: '#334155', background: '#f1f5f9', padding: '0.2rem 0.5rem', borderRadius: '999px' }}>
                    <div style={{
                      width: '16px',
                      height: '16px',
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #6366f1, #a855f7)',
                      color: 'white',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '0.55rem',
                      fontWeight: 'bold'
                    }}>
                      {u.first_name?.[0] || u.email[0].toUpperCase()}
                    </div>
                    <span>{u.first_name || u.email}</span>
                  </div>
                ))}
              </div>
            ) : (
              <span style={{ fontSize: '0.8rem', color: '#94a3b8', fontStyle: 'italic', marginBottom: '0.5rem' }}>Unassigned</span>
            )}
            <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b' }}>Assignee Allocation:</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                <select
                  style={{
                    padding: '0.4rem',
                    borderRadius: '6px',
                    border: '1px solid #cbd5e1',
                    fontSize: '0.8rem',
                    color: '#334155',
                    outline: 'none',
                    width: '100%'
                  }}
                  value={(activeTask.assignees || activeTask.assignee_details?.map(d => d.id) || [])[0] || ''}
                  onChange={async (e) => {
                    const val = e.target.value;
                    try {
                      const updated = await updateOrgTask(selectedOrg.slug, activeTask.id, { assignees: val ? [val] : [] });
                      setActiveTask(updated);
                      handleLoadTasks();
                    } catch (err) {
                      console.error("Failed to update assignees:", err);
                    }
                  }}
                >
                  <option value="">Unassigned</option>
                  {orgMembers.map(m => {
                    const userId = m.user?.id || m.user_id;
                    const name = m.user?.first_name || m.user?.last_name ? `${m.user.first_name || ''} ${m.user.last_name || ''}`.trim() : m.email;
                    return (
                      <option key={userId} value={userId}>
                        {name}
                      </option>
                    );
                  })}
                </select>
              </div>
            </div>
          </div>
        </div>
        {/* Task Sharing Settings */}
        <div className="task-detail-meta-group" style={{ borderTop: '1px solid #f1f5f9', paddingTop: '1rem', marginBottom: '1rem' }}>
          <h4 className="task-detail-meta-label" style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <Lock size={14} /> Sharing & Permissions
          </h4>
          <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem', boxShadow: '0 1px 2px rgba(0,0,0,0.02)' }}>
            <button
              type="button"
              onClick={() => openSharingModal('activeTask', {
                ...activeTask,
                assignees: (activeTask.assignees || []).map(a => a.id || a.user_id || a),
                shared_viewers: (activeTask.shared_viewers || []).map(v => v.id || v.user_id || v)
              })}
              style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem', background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '8px', cursor: 'pointer', color: '#334155', fontWeight: 500, justifyContent: 'space-between', width: '100%', outline: 'none' }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Users size={16} style={{ color: '#6366f1' }} />
                <span>
                  {activeTask.sharing_option === 'private' ? 'Private' : activeTask.sharing_option === 'specific' ? 'Specific People' : 'Entire Workspace'}
                </span>
              </div>
            </button>
          </div>
        </div>
        <div style={{ marginTop: 'auto', paddingTop: '1.25rem', borderTop: '1px solid #e2e8f0' }}>
          <button
            className="danger-btn-premium"
            style={{ width: '100%', justifyContent: 'center', padding: '0.6rem', fontSize: '0.85rem' }}
            onClick={() => {
              modal.showConfirmation('Are you sure you want to delete this task?', async () => {
                try {
                  await deleteOrgTask(selectedOrg.slug, activeTask.id);
                  modal.showSuccess('Task deleted successfully');
                  setTasksView('list');
                  handleLoadTasks();
                } catch (err) {
                  modal.showError("Failed to delete task or access denied.");
                }
              });
            }}
          >
            <Trash2 size={14} style={{ marginRight: '0.4rem' }} /> Delete Task
          </button>
        </div>
      </div>
    </div>
  );
}
return null;
            }) ()}
{
  activeTab === 'pending_queue' && (
    <PendingQueueView
      selectedOrg={selectedOrg}
      tasks={tasks}
      handleLoadTasks={handleLoadTasks}
      orgMembers={orgMembers}
      goals={goals}
      onEditTask={(task) => {
        setActiveTab('tasks');
        handleTaskClick(task);
      }}
    />
  )
}
{
  activeTab === 'permissions' && (
    <div className="permissions-view" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #e2e8f0', paddingBottom: '1rem' }}>
        <div>
          <h2 className="section-header" style={{ margin: 0 }}>Access Control & Permissions</h2>
          <p className="section-desc" style={{ margin: '0.25rem 0 0 0' }}>Manage roles, granular access privileges, and review team requests.</p>
        </div>
        {/* Tab Switcher */}
        <div style={{ display: 'flex', background: '#f1f5f9', padding: '0.25rem', borderRadius: '8px', gap: '0.25rem' }}>
          <button
            onClick={() => { setPermissionsSubTab('members'); setSelectedPermissionMember(null); }}
            style={{
              padding: '0.5rem 1rem',
              border: 'none',
              borderRadius: '6px',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer',
              background: permissionsSubTab === 'members' ? 'white' : 'transparent',
              color: permissionsSubTab === 'members' ? '#1e293b' : '#64748b',
              boxShadow: permissionsSubTab === 'members' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
              transition: 'all 0.2s'
            }}
          >
            Workspace Permissions
          </button>
          {(selectedOrg?.my_status?.role === 'owner' || selectedOrg?.my_status?.role === 'admin') && (
            <button
              onClick={() => { setPermissionsSubTab('requests'); setSelectedPermissionMember(null); }}
              style={{
                padding: '0.5rem 1rem',
                border: 'none',
                borderRadius: '6px',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
                background: permissionsSubTab === 'requests' ? 'white' : 'transparent',
                color: permissionsSubTab === 'requests' ? '#1e293b' : '#64748b',
                boxShadow: permissionsSubTab === 'requests' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}
            >
              Join Requests
              {joinRequests.length > 0 && (
                <span style={{ background: '#ef4444', color: 'white', fontSize: '0.75rem', padding: '0.1rem 0.4rem', borderRadius: '10px' }}>
                  {joinRequests.length}
                </span>
              )}
            </button>
          )}
        </div>
      </div>
      {(permissionsSubTab === 'requests' && (selectedOrg?.my_status?.role === 'owner' || selectedOrg?.my_status?.role === 'admin')) ? (
        <div className="requests-container">
          {activeJoinRequest ? (
            <div className="request-detail-view" style={{ background: 'white', borderRadius: '16px', border: '1px solid #e2e8f0', padding: '2rem', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.02)' }}>
              <button
                className="back-btn-smooth"
                onClick={() => setActiveJoinRequest(null)}
                style={{ background: '#f8fafc', border: '1px solid #e2e8f0', padding: '0.4rem 0.8rem', borderRadius: '20px', color: '#475569', display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '1.5rem', cursor: 'pointer', fontSize: '0.85rem', fontWeight: 500, transition: 'all 0.2s', width: 'fit-content' }}
              >
                <ArrowLeft size={14} /> Back to Requests
              </button>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1.5rem', marginBottom: '2rem' }}>
                <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'linear-gradient(135deg, #6366f1, #818cf8)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem', fontWeight: 600 }}>
                  {activeJoinRequest.first_name ? activeJoinRequest.first_name[0].toUpperCase() : activeJoinRequest.email[0].toUpperCase()}
                </div>
                <div style={{ flex: 1 }}>
                  <h3 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0f172a', margin: '0 0 0.25rem 0' }}>
                    {activeJoinRequest.first_name || activeJoinRequest.last_name
                      ? `${activeJoinRequest.first_name} ${activeJoinRequest.last_name}`.trim()
                      : activeJoinRequest.email}
                  </h3>
                  <div style={{ color: '#64748b', fontSize: '0.95rem', marginBottom: '0.75rem' }}>{activeJoinRequest.email}</div>
                  <div style={{ display: 'flex', gap: '1rem', color: '#64748b', fontSize: '0.9rem' }}>
                    <span>Requested Role: <strong style={{ color: '#0f172a' }}>{activeJoinRequest.requested_role}</strong></span>
                    <span>Status: <strong style={{ color: '#d97706' }}>Pending</strong></span>
                    <span>Date: <strong>{new Date(activeJoinRequest.created_at).toLocaleDateString()}</strong></span>
                  </div>
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2.5rem' }}>
                <div style={{ background: '#f8fafc', padding: '1.5rem', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                  <h4 style={{ fontSize: '1rem', fontWeight: 600, color: '#1e293b', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <UserIcon size={16} /> Profile Details
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.9rem' }}>
                    <div style={{ display: 'flex' }}><span style={{ color: '#64748b', width: '100px' }}>Job Title:</span> <span style={{ color: '#0f172a', fontWeight: 500 }}>{activeJoinRequest.job_title || '-'}</span></div>
                    <div style={{ display: 'flex' }}><span style={{ color: '#64748b', width: '100px' }}>Department:</span> <span style={{ color: '#0f172a', fontWeight: 500 }}>{activeJoinRequest.department || '-'}</span></div>
                    <div style={{ display: 'flex' }}><span style={{ color: '#64748b', width: '100px' }}>Education:</span> <span style={{ color: '#0f172a', fontWeight: 500 }}>{activeJoinRequest.education || '-'}</span></div>
                  </div>
                  {activeJoinRequest.bio && (
                    <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px dashed #cbd5e1' }}>
                      <span style={{ color: '#64748b', display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem' }}>Bio</span>
                      <p style={{ margin: 0, color: '#334155', fontSize: '0.9rem', lineHeight: 1.5 }}>{activeJoinRequest.bio}</p>
                    </div>
                  )}
                </div>
                <div style={{ background: '#f8fafc', padding: '1.5rem', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                  <h4 style={{ fontSize: '1rem', fontWeight: 600, color: '#1e293b', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <MessageSquare size={16} /> Request Message
                  </h4>
                  <p style={{ color: '#475569', fontSize: '0.95rem', lineHeight: 1.6, fontStyle: 'italic', margin: 0 }}>
                    "{activeJoinRequest.message || 'No additional message provided.'}"
                  </p>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '1rem', borderTop: '1px solid #e2e8f0', paddingTop: '1.5rem' }}>
                <button className="approve-btn" style={{ padding: '0.75rem 1.5rem', fontSize: '1rem' }} onClick={() => handleManageRequest(activeJoinRequest.id, 'approve')}>
                  <CheckCircle2 size={18} style={{ marginRight: '0.5rem' }} /> Approve Request
                </button>
                <button className="deny-btn" style={{ padding: '0.75rem 1.5rem', fontSize: '1rem' }} onClick={() => handleManageRequest(activeJoinRequest.id, 'deny')}>
                  Deny Request
                </button>
              </div>
            </div>
          ) : (
            <>
              <div className="request-header">
                New User Requests <span className="request-count">{joinRequests.length}</span>
              </div>
              {joinRequests.length === 0 ? (
                <div className="empty-requests">
                  <CheckCircle2 size={40} color="#cbd5e1" />
                  <p>All caught up! No pending requests.</p>
                </div>
              ) : (
                <div className="request-list">
                  {joinRequests.map(req => (
                    <div key={req.id} className="request-item">
                      <div className="request-info">
                        <div
                          style={{ fontWeight: 600, fontSize: '1rem', color: '#0f172a', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                          onClick={() => setActiveJoinRequest(req)}
                          className="hover-underline"
                        >
                          {req.email} <ArrowRight size={14} color="#6366f1" />
                        </div>
                        <div className="request-meta">
                          Requested: <span className="role-chip">{req.requested_role}</span>
                          Status: <span className="status-chip pending">Pending</span>
                        </div>
                        {req.message && <div className="request-message" style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '300px' }}>"{req.message}"</div>}
                      </div>
                      <div className="request-actions">
                        <button className="approve-btn" onClick={() => handleManageRequest(req.id, 'approve')}>Approve</button>
                        <button className="deny-btn" onClick={() => handleManageRequest(req.id, 'deny')}>Deny</button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      ) : (
        /* Granular Roles & Members list with Split Panel */
        <div style={{ display: 'flex', gap: selectedPermissionMember ? '0' : '1.5rem', flex: 1, minHeight: 0 }}>
          {/* Left/Main Column: Members List */}
          <div style={{ display: 'flex', flexDirection: 'column', background: 'white', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '1.25rem', overflow: 'hidden', width: selectedPermissionMember ? `${permissionsSidebarWidth}px` : '100%', flexShrink: 0 }}>
            <div style={{ fontWeight: 600, fontSize: '1rem', color: '#1e293b', marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>Workspace Members ({orgMembers.length})</span>
              <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 400 }}>Click member to set permissions</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', overflowY: 'auto', flex: 1 }}>
              {orgMembers.map(member => {
                const isSelf = member.email.toLowerCase() === sessionStorage.getItem('email')?.toLowerCase();
                const isSelected = selectedPermissionMember?.id === member.id;
                return (
                  <div
                    key={member.id}
                    onClick={() => {
                      // Allow Owners and Admins to manage members, maintain hierarchy
                      const myRole = selectedOrg?.my_status?.role;
                      if (myRole === 'owner' || myRole === 'admin') {
                        setSelectedPermissionMember(member);
                      }
                    }}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '0.75rem 1rem',
                      borderRadius: '10px',
                      background: isSelected ? '#f1f5f9' : 'white',
                      border: isSelected ? '1px solid #cbd5e1' : '1px solid #e2e8f0',
                      cursor: (selectedOrg?.my_status?.role === 'owner' || selectedOrg?.my_status?.role === 'admin') ? 'pointer' : 'default',
                      transition: 'all 0.15s'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <div style={{
                        width: '36px',
                        height: '36px',
                        borderRadius: '50%',
                        background: 'linear-gradient(135deg, #818cf8, #6366f1)',
                        color: 'white',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 600,
                        fontSize: '0.85rem'
                      }}>
                        {member.email[0].toUpperCase()}
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <div style={{ fontSize: '0.88rem', fontWeight: 600, color: '#1e293b', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                          {member.email}
                          {isSelf && <span style={{ fontSize: '0.7rem', background: '#e0f2fe', color: '#0369a1', padding: '0.1rem 0.35rem', borderRadius: '4px' }}>You</span>}
                          {member.is_on_leave && (
                            <span style={{ fontSize: '0.7rem', backgroundColor: '#fee2e2', color: '#b91c1c', padding: '0.1rem 0.35rem', borderRadius: '4px', fontWeight: 'bold' }}>On Leave</span>
                          )}
                        </div>
                        <div style={{ fontSize: '0.78rem', color: '#64748b', textTransform: 'capitalize' }}>
                          Role: <strong style={{ color: '#475569' }}>{member.role}</strong>
                        </div>
                      </div>
                    </div>
                    <ChevronRight size={16} color={isSelected ? '#6366f1' : '#94a3b8'} />
                  </div>
                );
              })}
            </div>
          </div>
          {/* Resize Handle */}
          {selectedPermissionMember && (
            <div
              onMouseDown={handlePermissionsSidebarResize}
              style={{
                width: '6px',
                cursor: 'col-resize',
                alignSelf: 'stretch',
                background: '#e2e8f0',
                margin: '0 8px',
                zIndex: 10,
                transition: 'background 0.2s',
                borderRadius: '3px',
                flexShrink: 0
              }}
              onMouseEnter={(e) => e.target.style.background = '#6366f1'}
              onMouseLeave={(e) => e.target.style.background = '#e2e8f0'}
            />
          )}
          {/* Right Column: Active Permissions Editor for Selected Member */}
          {selectedPermissionMember && (() => {
            const myRole = selectedOrg?.my_status?.role;
            const targetRole = selectedPermissionMember.role;
            // Check hierarchical rules
            const isOwnerEditingSelf = myRole === 'owner' && targetRole === 'owner';
            const isOwnerEditingOther = myRole === 'owner' && targetRole !== 'owner';
            const isAdminEditingMember = myRole === 'admin' && targetRole === 'member';
            const isEditable = isOwnerEditingOther || isAdminEditingMember;
            // Build target permission state
            const targetPerms = selectedPermissionMember.custom_permissions || {};
            const togglePerm = (permKey, currentVal) => {
              if (!isEditable) return;
              const newPerms = { ...targetPerms, [permKey]: !currentVal };
              handleChangePermissions(selectedPermissionMember.id, newPerms);
            };
            const permissionsList = [
              { section: 'Goals Permissions' },
              { key: 'create_workspace_goals', label: 'Create Workspace Goals', desc: 'Allows user to create new goals.' },
              { key: 'view_all_goals', label: 'View All Goals', desc: 'Allows user to see all goals across the workspace.' },
              { key: 'edit_goals', label: 'Edit & Update Goals', desc: 'Allows workspace-wide editing of all goals.' },
              { key: 'delete_workspace_goals', label: 'Delete Workspace Goals', desc: 'Allows user to permanently delete goals.' },
              { key: 'manage_goal_visibility', label: 'Manage Goal Visibility', desc: 'Allows changing a goal\'s sharing settings.' },
              { key: 'assign_goals', label: 'Assign Goals', desc: 'Allows assigning goals to other users.' },
              { section: 'Tasks Permissions' },
              { key: 'create_workspace_tasks', label: 'Create Workspace Tasks', desc: 'Allows user to create new tasks.' },
              { key: 'view_all_tasks', label: 'View All Tasks', desc: 'Allows user to see all tasks across the workspace.' },
              { key: 'edit_tasks', label: 'Edit & Update Tasks', desc: 'Allows workspace-wide editing of all tasks.' },
              { key: 'delete_workspace_tasks', label: 'Delete Workspace Tasks', desc: 'Allows user to permanently delete tasks.' },
              { key: 'manage_task_visibility', label: 'Manage Task Visibility', desc: 'Allows changing a task\'s sharing settings.' },
              { key: 'assign_tasks', label: 'Assign Tasks', desc: 'Allows assigning tasks to other users.' },
              { key: 'manage_task_comments', label: 'Manage Task Comments', desc: 'Allows adding and editing comments.' },
              { key: 'manage_task_attachments', label: 'Manage Task Attachments', desc: 'Allows uploading and deleting file attachments.' },
              { section: 'Team & Workspace Permissions' },
              { key: 'invite_workspace_members', label: 'Invite Workspace Members', desc: 'Allows sending email invitations.' },
              { key: 'remove_workspace_members', label: 'Remove Workspace Members', desc: 'Allows removing standard members.' },
              { key: 'change_roles', label: 'Change Member Roles', desc: 'Allows promoting members to Admin status.' },
              { key: 'view_member_profiles', label: 'View Member Profiles', desc: 'Allows viewing team directory.' },
              { key: 'manage_workspace_settings', label: 'Manage Workspace Settings', desc: 'Allows editing workspace profile, logo, description.' },
            ];
            // Define defaults to show what standard role permits
            const getRoleDefaults = (role) => {
              if (role === 'owner' || role === 'admin') {
                return {
                  create_workspace_goals: true, view_all_goals: true, edit_goals: true, delete_workspace_goals: true, manage_goal_visibility: true, assign_goals: true,
                  create_workspace_tasks: true, view_all_tasks: true, edit_tasks: true, delete_workspace_tasks: true, manage_task_visibility: true, assign_tasks: true, manage_task_comments: true, manage_task_attachments: true,
                  invite_workspace_members: true, remove_workspace_members: true, change_roles: true, view_member_profiles: true, manage_workspace_settings: true,
                };
              }
              return {
                create_workspace_goals: true, view_all_goals: false, edit_goals: false, delete_workspace_goals: false, manage_goal_visibility: false, assign_goals: false,
                create_workspace_tasks: true, view_all_tasks: false, edit_tasks: false, delete_workspace_tasks: false, manage_task_visibility: false, assign_tasks: false, manage_task_comments: true, manage_task_attachments: true,
                invite_workspace_members: false, remove_workspace_members: false, change_roles: false, view_member_profiles: true, manage_workspace_settings: false,
              };
            };
            const defaults = getRoleDefaults(targetRole);
            return (
              <div style={{ display: 'flex', flexDirection: 'column', background: 'white', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '1.25rem', overflow: 'hidden' }}>
                <div style={{ borderBottom: '1px solid #f1f5f9', paddingBottom: '0.85rem', marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#1e293b' }}>
                      Manage Permissions
                    </div>
                    <div style={{ fontSize: '0.82rem', color: '#64748b', marginTop: '0.15rem' }}>
                      {selectedPermissionMember.email} ({selectedPermissionMember.role})
                    </div>
                  </div>
                  {/* Role management switcher if owner */}
                  {myRole === 'owner' && targetRole !== 'owner' && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600 }}>Role:</span>
                      <select
                        value={targetRole}
                        onChange={(e) => {
                          const newRole = e.target.value;
                          modal.showConfirmation(`Are you sure you want to change role to ${newRole}?`, () => {
                            handleChangeRole(selectedPermissionMember.id, newRole);
                          });
                        }}
                        style={{
                          padding: '0.35rem 0.65rem',
                          borderRadius: '6px',
                          border: '1px solid #cbd5e1',
                          fontSize: '0.8rem',
                          fontWeight: 600,
                          background: 'white',
                          cursor: 'pointer'
                        }}
                      >
                        <option value="member">Member</option>
                        <option value="admin">Admin</option>
                        <option value="owner">Promote to Owner</option>
                      </select>
                    </div>
                  )}
                </div>
                {/* Permission Status Banner */}
                {!isEditable && (
                  <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '0.75rem 1rem', fontSize: '0.8rem', color: '#64748b', marginBottom: '1rem', lineHeight: 1.4 }}>
                    ℹ️ <strong>Read-Only Access:</strong> You cannot modify permissions of an <strong>{targetRole}</strong> role due to the organization hierarchy controls.
                  </div>
                )}
                {isEditable && (
                  <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '8px', padding: '0.75rem 1rem', fontSize: '0.8rem', color: '#166534', marginBottom: '1rem', lineHeight: 1.4 }}>
                    ✅ <strong>Custom Override Enabled:</strong> You can toggle granular checkmarks below to selectively grant or revoke specific privileges for this member.
                  </div>
                )}
                {/* List of checkboxes */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', overflowY: 'auto', flex: 1 }}>
                  {permissionsList.map((item, idx) => {
                    if (item.section) {
                      return (
                        <div key={'section-' + idx} style={{ marginTop: '1rem', borderBottom: '1px solid #e2e8f0', paddingBottom: '0.4rem' }}>
                          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            {item.section}
                          </span>
                        </div>
                      );
                    }
                    const { key, label, desc } = item;
                    // Active permission value is override if set, otherwise standard role default
                    const hasOverride = key in targetPerms;
                    const activeVal = hasOverride ? !!targetPerms[key] : defaults[key];
                    return (
                      <div
                        key={key}
                        style={{
                          display: 'flex',
                          alignItems: 'flex-start',
                          gap: '0.85rem',
                          padding: '0.85rem',
                          borderRadius: '8px',
                          background: activeVal ? '#f8fafc' : '#ffffff',
                          border: activeVal ? '1px dashed #cbd5e1' : '1px solid #f1f5f9',
                          opacity: isEditable ? 1 : 0.85
                        }}
                      >
                        <input
                          type="checkbox"
                          id={`chk-${key}`}
                          checked={activeVal}
                          disabled={!isEditable}
                          onChange={() => togglePerm(key, activeVal)}
                          style={{
                            marginTop: '0.2rem',
                            width: '16px',
                            height: '16px',
                            cursor: isEditable ? 'pointer' : 'not-allowed',
                            accentColor: '#6366f1'
                          }}
                        />
                        <label
                          htmlFor={`chk-${key}`}
                          style={{
                            display: 'flex',
                            flexDirection: 'column',
                            cursor: isEditable ? 'pointer' : 'not-allowed',
                            flex: 1
                          }}
                        >
                          <span style={{ fontSize: '0.88rem', fontWeight: 600, color: '#1e293b', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            {label}
                            {hasOverride && (
                              <span style={{ fontSize: '0.65rem', background: '#f5f3ff', color: '#6366f1', padding: '0.05rem 0.35rem', borderRadius: '4px', border: '1px solid #ddd6fe' }}>
                                Custom Override
                              </span>
                            )}
                          </span>
                          <span style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '0.15rem' }}>{desc}</span>
                        </label>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  )
}
{
  activeTab === 'members' && (() => {
    if (selectedMemberId) {
      const member = orgMembers.find(m => m.id === selectedMemberId);
      if (!member) {
        return (
          <div className="members-view">
            <button className="note-save-btn" onClick={() => setSelectedMemberId(null)} style={{ background: '#f1f5f9', border: 'none', color: '#475569', padding: '0.5rem 1.25rem', borderRadius: '6px', cursor: 'pointer', marginBottom: '1rem' }}>
              &larr; Back to Members
            </button>
            <div className="error-message">Member not found.</div>
          </div>
        );
      }
      const isSelf = member.email.toLowerCase() === sessionStorage.getItem('email')?.toLowerCase();
      const isUserOwner = selectedOrg?.my_status?.role === 'owner';
      const isTargetOwner = member.role === 'owner';
      const isTargetAdmin = member.role === 'admin';
      const canManage = !isSelf && (isUserOwner || (selectedOrg?.my_status?.role === 'admin' && !isTargetOwner && !isTargetAdmin));
      const u = member.user || {};
      const canViewScheduleInfo = isMemberScheduleViewer();
      const memberStats = canViewScheduleInfo ? getMemberStats(member) : null;
      const schedule = memberStats?.schedule || {};
      const avatarChar = member.email?.[0]?.toUpperCase() || 'U';
      return (
        <div className="members-view">
          <button className="note-save-btn" onClick={() => setSelectedMemberId(null)} style={{ background: '#f1f5f9', border: 'none', color: '#475569', padding: '0.5rem 1.25rem', borderRadius: '6px', cursor: 'pointer', marginBottom: '1.5rem', display: 'inline-flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
            &larr; Back to Members List
          </button>
          <div className="premium-card-settings" style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '2rem', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03)', maxWidth: '800px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '2rem', borderBottom: '1px solid #f1f5f9', paddingBottom: '1.5rem', marginBottom: '1.5rem' }}>
              <div style={{ width: '96px', height: '96px', borderRadius: '50%', background: '#f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden', border: '2px solid #e2e8f0' }}>
                {u.profile_picture ? (
                  <img src={getLogoUrl(u.profile_picture)} alt="Profile" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                ) : (
                  <span style={{ fontSize: '2.5rem', fontWeight: 600, color: '#6366f1' }}>
                    {avatarChar}
                  </span>
                )}
              </div>
              <div style={{ textAlign: 'left' }}>
                <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
                  {u.first_name || u.last_name ? `${u.first_name || ''} ${u.last_name || ''}` : 'Unnamed Member'}
                </h2>
                <p style={{ fontSize: '0.9rem', color: '#64748b', margin: '0.25rem 0 0 0' }}>
                  {member.email}
                </p>
                <span className={`member-role-badge-premium role-${member.role}`} style={{ marginTop: '0.5rem', display: 'inline-block' }}>
                  {member.role.toUpperCase()}
                </span>
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem', textAlign: 'left' }}>
              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Job Title</label>
                <p style={{ fontSize: '0.95rem', color: '#334155', margin: '0.25rem 0 0 0', fontWeight: 500 }}>
                  {u.job_title || 'N/A'}
                </p>
              </div>
              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Department</label>
                <p style={{ fontSize: '0.95rem', color: '#334155', margin: '0.25rem 0 0 0', fontWeight: 500 }}>
                  {u.department || 'N/A'}
                </p>
              </div>
              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Education</label>
                <p style={{ fontSize: '0.95rem', color: '#334155', margin: '0.25rem 0 0 0', fontWeight: 500 }}>
                  {u.education || 'N/A'}
                </p>
              </div>
              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Phone Number</label>
                <p style={{ fontSize: '0.95rem', color: '#334155', margin: '0.25rem 0 0 0', fontWeight: 500 }}>
                  {u.phone || 'N/A'}
                </p>
              </div>
              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Date of Birth</label>
                <p style={{ fontSize: '0.95rem', color: '#334155', margin: '0.25rem 0 0 0', fontWeight: 500 }}>
                  {u.date_of_birth ? new Date(u.date_of_birth).toLocaleDateString() : 'N/A'}
                </p>
              </div>
              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Joined Workspace</label>
                <p style={{ fontSize: '0.95rem', color: '#334155', margin: '0.25rem 0 0 0', fontWeight: 500 }}>
                  {new Date(member.joined_at).toLocaleDateString()}
                </p>
              </div>
            </div>
            <div style={{ marginBottom: '2rem', textAlign: 'left' }}>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Bio / Description</label>
              <p style={{ fontSize: '0.95rem', color: '#334155', margin: '0.25rem 0 0 0', lineHeight: 1.5 }}>
                {u.bio || 'No bio provided.'}
              </p>
            </div>
            {canViewScheduleInfo && (
              <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '1.5rem', marginTop: '1.5rem', textAlign: 'left' }}>
                <h3 style={{ margin: '0 0 1rem 0', fontSize: '1rem', color: '#0f172a', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Clock size={16} /> Schedule & Work History
                </h3>

                {/* Schedule visibility is intentionally restricted to owners, creators, and admins. */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '0.75rem', marginBottom: '1rem' }}>
                  {[
                    ['Work Start', formatScheduleTime(schedule.work_start_time)],
                    ['Work End', formatScheduleTime(schedule.work_end_time)],
                    ['Lunch Break', `${formatScheduleTime(schedule.lunch_break_start)} - ${formatScheduleTime(schedule.lunch_break_end)}`],
                    ['Tea Break', `${formatScheduleTime(schedule.tea_break_start)} - ${formatScheduleTime(schedule.tea_break_end)}`],
                    ['Time Spent', formatDurationMinutes(memberStats.totalSpentMinutes)],
                    ['Scheduled Tasks', `${memberStats.scheduledTasks.length}`],
                  ].map(([label, value]) => (
                    <div key={label} style={{ border: '1px solid #e2e8f0', borderRadius: '8px', padding: '0.85rem', background: '#f8fafc' }}>
                      <div style={{ fontSize: '0.68rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</div>
                      <div style={{ marginTop: '0.25rem', color: '#0f172a', fontWeight: 700, fontSize: '0.9rem' }}>{value}</div>
                    </div>
                  ))}
                </div>

                <div style={{ marginBottom: '1rem' }}>
                  <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.85rem', color: '#334155', fontWeight: 700 }}>Holidays, Half-days & Leaves</h4>
                  {memberStats.leaves.length === 0 ? (
                    <div style={{ color: '#64748b', fontSize: '0.85rem', padding: '0.75rem', border: '1px dashed #cbd5e1', borderRadius: '8px' }}>
                      No leave, half-day, or holiday records available for this member.
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      {memberStats.leaves.map(leave => (
                        <div key={leave.id || `${leave.leave_type}-${leave.start_date}`} style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', padding: '0.75rem', border: '1px solid #e2e8f0', borderRadius: '8px', background: 'white' }}>
                          <div>
                            <div style={{ color: '#0f172a', fontWeight: 700, fontSize: '0.85rem' }}>
                              {leave.leave_type || 'Leave'}{Number(leave.number_of_days) === 0.5 ? ' (Half-day)' : ''}
                            </div>
                            <div style={{ color: '#64748b', fontSize: '0.78rem', marginTop: '0.15rem' }}>
                              {leave.start_date ? new Date(leave.start_date).toLocaleDateString() : 'N/A'} to {leave.end_date ? new Date(leave.end_date).toLocaleDateString() : 'N/A'}
                            </div>
                          </div>
                          <span style={{ alignSelf: 'center', fontSize: '0.72rem', fontWeight: 700, color: leave.status === 'Approved' ? '#047857' : '#92400e', background: leave.status === 'Approved' ? '#d1fae5' : '#fef3c7', padding: '0.2rem 0.5rem', borderRadius: '999px' }}>
                            {leave.status || 'Pending'}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div>
                  <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.85rem', color: '#334155', fontWeight: 700 }}>Scheduled Task Dates & Times</h4>
                  {memberStats.scheduledTasks.length === 0 ? (
                    <div style={{ color: '#64748b', fontSize: '0.85rem', padding: '0.75rem', border: '1px dashed #cbd5e1', borderRadius: '8px' }}>
                      No scheduled task history available.
                    </div>
                  ) : (
                    <div style={{ border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden' }}>
                      {memberStats.scheduledTasks.map(task => (
                        <div key={task.id} style={{ display: 'grid', gridTemplateColumns: 'minmax(160px, 1fr) minmax(150px, auto) minmax(150px, auto)', gap: '1rem', padding: '0.75rem', borderBottom: '1px solid #f1f5f9', alignItems: 'center', background: 'white' }}>
                          <div>
                            <div style={{ color: '#0f172a', fontWeight: 700, fontSize: '0.85rem' }}>{task.title || 'Untitled task'}</div>
                            <div style={{ color: '#64748b', fontSize: '0.75rem', marginTop: '0.15rem' }}>{task.status || task.schedule_status || 'scheduled'}</div>
                          </div>
                          <div style={{ color: '#334155', fontSize: '0.78rem' }}>Start: {formatTaskDateTime(task.planned_start)}</div>
                          <div style={{ color: '#334155', fontSize: '0.78rem' }}>End: {formatTaskDateTime(task.planned_end)}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
            {canManage && (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid #f1f5f9', paddingTop: '1.5rem', marginTop: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 600, color: '#475569' }}>Change Member Role:</label>
                  <select
                    className="select-role-premium"
                    value={member.role}
                    onChange={(e) => handleChangeRole(member.id, e.target.value)}
                    disabled={loading}
                    style={{ width: 'auto' }}
                  >
                    <option value="member">Member</option>
                    <option value="admin">Admin</option>
                    {isUserOwner && <option value="owner">Promote to Owner</option>}
                  </select>
                </div>
                <button
                  className="remove-btn-premium"
                  onClick={async () => {
                    await handleRemoveMember(member.id);
                    setSelectedMemberId(null);
                  }}
                  disabled={loading}
                >
                  Remove from Workspace
                </button>
              </div>
            )}
          </div>
        </div>
      );
    }
    return (
      <div className="members-view">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem', gap: '2rem' }}>
          <div style={{ flex: 1 }}>
            <h2 className="section-title-premium">Members Management</h2>
            <p className="section-subtitle-premium" style={{ marginBottom: 0 }}>
              Manage roles, view member profiles, transfer ownership, or remove colleagues.
            </p>
          </div>
          <div style={{ display: 'flex', gap: '1rem', flexShrink: 0 }}>
            <button className="btn-primary" onClick={() => setView('collaborate')} style={{ width: 'auto', padding: '0.6rem 1.2rem', background: 'linear-gradient(135deg, #1e293b, #334155)' }}>
              <Users size={16} style={{ marginRight: '0.5rem' }} /> Join
            </button>
            {(selectedOrg?.my_status?.role === 'owner' || selectedOrg?.my_status?.role === 'admin') && (
              <button className="btn-primary" onClick={() => setShowInviteModal(true)} style={{ width: 'auto', padding: '0.6rem 1.2rem' }}>
                <Plus size={16} style={{ marginRight: '0.5rem' }} /> Invite Member
              </button>
            )}
          </div>
        </div>
        {error && <div className="error-message" style={{ marginBottom: '1.5rem' }}>{error}</div>}
        {message && <div className="success-message" style={{ marginBottom: '1.5rem' }}>{message}</div>}
        <div className="members-list-card">
          {orgMembers.map(member => {
            const isSelf = member.email.toLowerCase() === sessionStorage.getItem('email')?.toLowerCase();
            const isUserOwner = selectedOrg?.my_status?.role === 'owner';
            const isTargetOwner = member.role === 'owner';
            const isTargetAdmin = member.role === 'admin';
            const canManage = !isSelf && (isUserOwner || (selectedOrg?.my_status?.role === 'admin' && !isTargetOwner && !isTargetAdmin));
            const u = member.user || {};
            const canViewScheduleInfo = isMemberScheduleViewer();
            const memberStats = canViewScheduleInfo ? getMemberStats(member) : null;
            const schedule = memberStats?.schedule || {};
            return (
              <div key={member.id} className="member-row-premium" style={{ cursor: 'pointer' }} onClick={() => setSelectedMemberId(member.id)}>
                <div className="member-user-info">
                  <div className="member-avatar-circle">
                    {u.profile_picture ? (
                      <img src={getLogoUrl(u.profile_picture)} alt="Avatar" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                    ) : (
                      member.email[0].toUpperCase()
                    )}
                  </div>
                  <div style={{ textAlign: 'left' }}>
                    <div className="member-user-email" style={{ fontWeight: 600, color: '#1e293b', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                      {u.first_name || u.last_name ? `${u.first_name || ''} ${u.last_name || ''}` : member.email}
                      {isSelf && <span style={{ color: '#6366f1', fontSize: '0.8rem', fontWeight: 500 }}>(You)</span>}
                      {member.is_on_leave && (
                        <span style={{ color: '#b91c1c', fontSize: '0.75rem', fontWeight: 'bold', backgroundColor: '#fee2e2', padding: '0.1rem 0.35rem', borderRadius: '4px' }}>On Leave</span>
                      )}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#64748b', textAlign: 'left', marginTop: '0.15rem' }}>
                      {u.job_title ? `${u.job_title} • ` : ''}Joined {new Date(member.joined_at).toLocaleDateString()}
                    </div>
                    {canViewScheduleInfo && (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', marginTop: '0.5rem' }}>
                        {/* Compact member schedule summary for owner/admin/creator list view. */}
                        <span style={{ fontSize: '0.7rem', color: '#334155', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: '999px', padding: '0.18rem 0.5rem' }}>
                          Work {formatScheduleTime(schedule.work_start_time)}-{formatScheduleTime(schedule.work_end_time)}
                        </span>
                        <span style={{ fontSize: '0.7rem', color: '#334155', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '999px', padding: '0.18rem 0.5rem' }}>
                          Spent {formatDurationMinutes(memberStats.totalSpentMinutes)}
                        </span>
                        <span style={{ fontSize: '0.7rem', color: '#334155', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '999px', padding: '0.18rem 0.5rem' }}>
                          {memberStats.scheduledTasks.length} scheduled
                        </span>
                        {memberStats.leaves.length > 0 && (
                          <span style={{ fontSize: '0.7rem', color: '#92400e', background: '#fef3c7', border: '1px solid #fde68a', borderRadius: '999px', padding: '0.18rem 0.5rem' }}>
                            {memberStats.leaves.length} leave record{memberStats.leaves.length === 1 ? '' : 's'}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }} onClick={e => e.stopPropagation()}>
                  {!canManage ? (
                    <span className={`member-role-badge-premium role-${member.role}`}>
                      {member.role}
                    </span>
                  ) : (
                    <>
                      <select
                        className="select-role-premium"
                        value={member.role}
                        onChange={(e) => handleChangeRole(member.id, e.target.value)}
                        disabled={loading}
                      >
                        <option value="member">Member</option>
                        <option value="admin">Admin</option>
                        {isUserOwner && <option value="owner">Promote to Owner</option>}
                      </select>
                      <button
                        className="remove-btn-premium"
                        onClick={() => handleRemoveMember(member.id)}
                        disabled={loading}
                      >
                        Remove
                      </button>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Pending Invitations Section */}
        {pendingInvites && pendingInvites.length > 0 && (
          <div style={{ marginTop: '2.5rem' }}>
            <h3 className="section-title-premium" style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>Pending Invitations</h3>
            <div className="members-list-card">
              {pendingInvites.map(invite => (
                <div key={invite.id} className="member-row-premium">
                  <div className="member-user-info">
                    <div className="member-avatar-circle" style={{ background: '#f1f5f9', color: '#64748b' }}>
                      <Mail size={16} />
                    </div>
                    <div style={{ textAlign: 'left' }}>
                      <div className="member-user-email" style={{ fontWeight: 600, color: '#1e293b' }}>
                        {invite.email}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.15rem' }}>
                        Invited as {invite.role} • Expires {new Date(invite.expires_at).toLocaleDateString()}
                      </div>
                      {invite.message && (
                        <div style={{ fontSize: '0.8rem', color: '#475569', marginTop: '0.25rem', fontStyle: 'italic' }}>
                          "{invite.message}"
                        </div>
                      )}
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <span style={{ fontSize: '0.8rem', padding: '0.2rem 0.6rem', borderRadius: '12px', background: '#fef3c7', color: '#d97706', fontWeight: 600 }}>
                      Pending
                    </span>
                    {(selectedOrg?.my_status?.role === 'owner' || selectedOrg?.my_status?.role === 'admin') && (
                      <button
                        className="remove-btn-premium"
                        onClick={() => handleCancelInvitation(invite.id)}
                        disabled={loading}
                      >
                        Cancel
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  })()
}
{
  activeTab === 'profile' && (
    <div className="profile-view" style={{ maxWidth: '720px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem', padding: '0.5rem' }}>
      <div>
        <h2 className="section-title-premium" style={{ margin: 0 }}>User Profile Settings</h2>
        <p className="section-subtitle-premium" style={{ margin: '0.25rem 0 0 0' }}>
          Manage your personal profile, bio, job titles, education, contact info, and security.
        </p>
      </div>
      {error && <div className="error-message" style={{ marginBottom: '0.5rem' }}>{error}</div>}
      {message && <div className="success-message" style={{ marginBottom: '0.5rem' }}>{message}</div>}
      <div className="premium-card-settings" style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '1.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
        <form onSubmit={handleUpdateProfile} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div className="input-group" style={{ margin: 0 }}>
            <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>Profile Picture</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', marginTop: '0.5rem' }}>
              <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: '#f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden', border: '1px solid #e2e8f0' }}>
                {profileData.profile_picture_preview ? (
                  <img src={profileData.profile_picture_preview} alt="Profile" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                ) : (
                  <span style={{ fontSize: '1.5rem', fontWeight: 600, color: '#6366f1' }}>
                    {sessionStorage.getItem('email')?.[0].toUpperCase()}
                  </span>
                )}
              </div>
              <input
                type="file"
                accept="image/*"
                onChange={e => {
                  const file = e.target.files[0];
                  if (file) {
                    setProfileData({
                      ...profileData,
                      profile_picture: file,
                      profile_picture_preview: URL.createObjectURL(file)
                    });
                  }
                }}
                style={{ fontSize: '0.8rem', color: '#64748b' }}
              />
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="input-group" style={{ margin: 0 }}>
              <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>First Name</label>
              <input
                className="input-field"
                value={profileData.first_name}
                onChange={e => setProfileData({ ...profileData, first_name: e.target.value })}
                style={{ marginTop: '0.35rem' }}
              />
            </div>
            <div className="input-group" style={{ margin: 0 }}>
              <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>Last Name</label>
              <input
                className="input-field"
                value={profileData.last_name}
                onChange={e => setProfileData({ ...profileData, last_name: e.target.value })}
                style={{ marginTop: '0.35rem' }}
              />
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="input-group" style={{ margin: 0 }}>
              <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>Job Title</label>
              <input
                className="input-field"
                value={profileData.job_title}
                onChange={e => setProfileData({ ...profileData, job_title: e.target.value })}
                style={{ marginTop: '0.35rem' }}
              />
            </div>
            <div className="input-group" style={{ margin: 0 }}>
              <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>Department</label>
              <input
                className="input-field"
                value={profileData.department}
                onChange={e => setProfileData({ ...profileData, department: e.target.value })}
                style={{ marginTop: '0.35rem' }}
              />
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="input-group" style={{ margin: 0 }}>
              <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>Education</label>
              <input
                className="input-field"
                value={profileData.education}
                onChange={e => setProfileData({ ...profileData, education: e.target.value })}
                style={{ marginTop: '0.35rem' }}
              />
            </div>
            <div className="input-group" style={{ margin: 0 }}>
              <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>Date of Birth</label>
              <input
                type="date"
                className="input-field"
                value={profileData.date_of_birth}
                onChange={e => setProfileData({ ...profileData, date_of_birth: e.target.value })}
                style={{ marginTop: '0.35rem' }}
              />
            </div>
          </div>
          <div className="input-group" style={{ margin: 0 }}>
            <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>Phone Number</label>
            <input
              className="input-field"
              value={profileData.phone}
              onChange={e => setProfileData({ ...profileData, phone: e.target.value })}
              style={{ marginTop: '0.35rem' }}
            />
          </div>
          <div className="input-group" style={{ margin: 0 }}>
            <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>Bio</label>
            <textarea
              className="input-field"
              value={profileData.bio}
              onChange={e => setProfileData({ ...profileData, bio: e.target.value })}
              rows={3}
              style={{ marginTop: '0.35rem' }}
            />
          </div>

          <div style={{ marginTop: '2rem', marginBottom: '1rem', borderTop: '1px solid #e2e8f0', paddingTop: '1.5rem' }}>
            <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#1e293b', marginBottom: '1rem' }}>Working Schedule</h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="input-group" style={{ margin: 0 }}>
                  <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>Work Start Time</label>
                  <input
                    type="time"
                    className="input-field"
                    value={profileData.work_start_time}
                    onChange={e => setProfileData({ ...profileData, work_start_time: e.target.value })}
                    style={{ marginTop: '0.35rem' }}
                  />
                </div>
                <div className="input-group" style={{ margin: 0 }}>
                  <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>Work End Time</label>
                  <input
                    type="time"
                    className="input-field"
                    value={profileData.work_end_time}
                    onChange={e => setProfileData({ ...profileData, work_end_time: e.target.value })}
                    style={{ marginTop: '0.35rem' }}
                  />
                </div>

              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="input-group" style={{ margin: 0 }}>
                  <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>Lunch Break Start</label>
                  <input
                    type="time"
                    className="input-field"
                    value={profileData.lunch_break_start}
                    onChange={e => {
                      const start = e.target.value;
                      let updates = { lunch_break_start: start };
                      if (start) {
                        const [h, m] = start.split(':').map(Number);
                        const newMins = h * 60 + m + 60; // Auto fill +60 min
                        const endH = Math.floor(newMins / 60) % 24;
                        const endM = newMins % 60;
                        updates.lunch_break_end = `${String(endH).padStart(2, '0')}:${String(endM).padStart(2, '0')}`;
                      }
                      setProfileData({ ...profileData, ...updates });
                    }}
                    style={{ marginTop: '0.35rem' }}
                  />
                </div>
                <div className="input-group" style={{ margin: 0 }}>
                  <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>Lunch Break End</label>
                  <input
                    type="time"
                    className="input-field"
                    value={profileData.lunch_break_end}
                    onChange={e => setProfileData({ ...profileData, lunch_break_end: e.target.value })}
                    style={{ marginTop: '0.35rem' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="input-group" style={{ margin: 0 }}>
                  <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>Tea Break Start</label>
                  <input
                    type="time"
                    className="input-field"
                    value={profileData.tea_break_start}
                    onChange={e => {
                      const start = e.target.value;
                      let updates = { tea_break_start: start };
                      if (start) {
                        const [h, m] = start.split(':').map(Number);
                        const newMins = h * 60 + m + 30; // Auto fill +30 min
                        const endH = Math.floor(newMins / 60) % 24;
                        const endM = newMins % 60;
                        updates.tea_break_end = `${String(endH).padStart(2, '0')}:${String(endM).padStart(2, '0')}`;
                      }
                      setProfileData({ ...profileData, ...updates });
                    }}
                    style={{ marginTop: '0.35rem' }}
                  />
                </div>
                <div className="input-group" style={{ margin: 0 }}>
                  <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>Tea Break End</label>
                  <input
                    type="time"
                    className="input-field"
                    value={profileData.tea_break_end}
                    onChange={e => setProfileData({ ...profileData, tea_break_end: e.target.value })}
                    style={{ marginTop: '0.35rem' }}
                  />
                </div>
              </div>
            </div>
          </div>

          <button type="submit" className="btn-primary" style={{ width: 'auto', padding: '0.65rem 1.75rem', fontSize: '0.85rem', alignSelf: 'flex-start' }} disabled={loading}>
            {loading ? <Loader2 className="animate-spin" /> : 'Save Profile Details'}
          </button>
        </form>
      </div>
      {/* Email & Verification section */}
      <div className="premium-card-settings" style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '1.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#1e293b', margin: '0 0 1rem 0' }}>Update Email Address</h3>
        {emailChangeStep === 'request' ? (
          <form onSubmit={handleRequestEmailChangeSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div className="input-group" style={{ margin: 0 }}>
              <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>New Email Address</label>
              <input
                type="email"
                className="input-field"
                value={newEmail}
                onChange={e => setNewEmail(e.target.value)}
                required
                style={{ marginTop: '0.35rem' }}
              />
            </div>
            <div className="input-group" style={{ margin: 0 }}>
              <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>Confirm Password</label>
              <div className="password-wrapper" style={{ marginTop: '0.35rem' }}>
                <input
                  type={showPassword ? "text" : "password"}
                  className="input-field"
                  value={emailChangePassword}
                  onChange={e => setEmailChangePassword(e.target.value)}
                  required
                  style={{ margin: 0 }}
                />
                <button type="button" className="eye-btn" onClick={() => setShowPassword(!showPassword)}>
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>
            <button type="submit" className="btn-primary" style={{ width: 'auto', padding: '0.65rem 1.75rem', fontSize: '0.85rem', alignSelf: 'flex-start' }} disabled={loading}>
              {loading ? <Loader2 className="animate-spin" /> : 'Send OTP to New Email'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyEmailChangeSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <p style={{ fontSize: '0.825rem', color: '#64748b', margin: 0 }}>
              We sent a 6-digit verification code to <strong>{newEmail}</strong>. Enter it below to verify and update your primary email.
            </p>
            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center', marginTop: '0.25rem' }}>
              {emailOtp.map((digit, idx) => (
                <input
                  key={idx}
                  type="text"
                  maxLength="1"
                  value={digit}
                  onChange={(e) => {
                    const val = e.target.value;
                    const nextOtp = [...emailOtp];
                    nextOtp[idx] = val;
                    setEmailOtp(nextOtp);
                    if (val && idx < 5) {
                      const nextEl = document.getElementById(`email-otp-${idx + 1}`);
                      if (nextEl) nextEl.focus();
                    }
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Backspace' && !emailOtp[idx] && idx > 0) {
                      const prevEl = document.getElementById(`email-otp-${idx - 1}`);
                      if (prevEl) prevEl.focus();
                    }
                  }}
                  id={`email-otp-${idx}`}
                  style={{ width: '40px', height: '40px', textAlign: 'center', fontSize: '1.25rem', border: '1px solid #cbd5e1', borderRadius: '8px', background: '#f8fafc' }}
                />
              ))}
            </div>
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
              <button type="button" className="note-save-btn" onClick={() => setEmailChangeStep('request')} style={{ padding: '0.5rem 1.25rem', background: '#f1f5f9', border: 'none', color: '#475569', borderRadius: '6px', cursor: 'pointer' }}>
                Cancel
              </button>
              <button type="submit" className="btn-primary" style={{ width: 'auto', padding: '0.5rem 1.5rem' }} disabled={loading}>
                {loading ? <Loader2 className="animate-spin" /> : 'Confirm Update'}
              </button>
            </div>
          </form>
        )}
      </div>
      {/* Change Password section */}
      <div className="premium-card-settings" style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '1.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#1e293b', margin: '0 0 1rem 0' }}>Security & Credentials</h3>
        <form onSubmit={handleChangePasswordSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div className="input-group" style={{ margin: 0 }}>
            <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>New Password</label>
            <div className="password-wrapper" style={{ marginTop: '0.35rem' }}>
              <input
                type={showPassword ? "text" : "password"}
                className="input-field"
                value={changePasswordData.new_password}
                onChange={e => setChangePasswordData({ ...changePasswordData, new_password: e.target.value })}
                required
                style={{ margin: 0 }}
              />
              <button type="button" className="eye-btn" onClick={() => setShowPassword(!showPassword)}>
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
          </div>
          <div className="input-group" style={{ margin: 0 }}>
            <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>Confirm Password</label>
            <div className="password-wrapper" style={{ marginTop: '0.35rem' }}>
              <input
                type={showPassword ? "text" : "password"}
                className="input-field"
                value={changePasswordData.confirm_password}
                onChange={e => setChangePasswordData({ ...changePasswordData, confirm_password: e.target.value })}
                required
                style={{ margin: 0 }}
              />
              <button type="button" className="eye-btn" onClick={() => setShowPassword(!showPassword)}>
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
          </div>
          <button type="submit" className="btn-primary" style={{ width: 'auto', padding: '0.65rem 1.75rem', fontSize: '0.85rem', alignSelf: 'flex-start' }} disabled={loading}>
            {loading ? <Loader2 className="animate-spin" /> : 'Update Password'}
          </button>
        </form>
      </div>
    </div>
  )
}
{
  activeTab === 'templates' && (
    <TemplateManager orgSlug={selectedOrg?.slug} onApplyTemplate={async (goalId) => {
      try {
        await handleLoadGoals();
        const detail = await getGoalDetail(goalId);
        setActiveGoal(detail);
        setGoalsView('detail');
        setActiveTab('goals');
      } catch (e) {
        console.error(e);
        setActiveTab('goals');
        setGoalsView('list');
      }
    }} />
  )
}
{
  activeTab === 'settings' && (selectedOrg?.my_status?.role === 'owner' || selectedOrg?.my_status?.role === 'admin') && (
    <div className="settings-view" style={{ maxWidth: '720px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem', padding: '0.5rem' }}>
      <div>
        <h2 className="section-title-premium" style={{ margin: 0 }}>Workspace Settings</h2>
        <p className="section-subtitle-premium" style={{ margin: '0.25rem 0 0 0' }}>
          Modify workspace info, logo identity, or perform soft deactivation.
        </p>
      </div>
      {error && <div className="error-message" style={{ marginBottom: '0.5rem' }}>{error}</div>}
      {message && <div className="success-message" style={{ marginBottom: '0.5rem' }}>{message}</div>}
      <div className="premium-card-settings" style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '1.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
        <form onSubmit={handleUpdateOrgSettings} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div className="input-group" style={{ margin: 0 }}>
            <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>Workspace Logo</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', marginTop: '0.5rem' }}>
              <div style={{ width: '64px', height: '64px', borderRadius: '12px', background: '#f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden', border: '1px solid #e2e8f0' }}>
                {selectedOrg?.logo ? (
                  <img src={selectedOrg.logo} alt="logo" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                ) : (
                  <Users size={24} style={{ color: '#94a3b8' }} />
                )}
              </div>
              <input
                type="file"
                accept="image/*"
                onChange={e => setEditOrgData({ ...editOrgData, logo: e.target.files[0] })}
                style={{ fontSize: '0.8rem', color: '#64748b' }}
              />
            </div>
          </div>
          <div className="input-group" style={{ margin: 0 }}>
            <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>Workspace Name</label>
            <input
              className="input-field"
              value={editOrgData.name}
              onChange={e => setEditOrgData({ ...editOrgData, name: e.target.value })}
              required
              style={{ marginTop: '0.35rem' }}
            />
          </div>
          <div className="input-group" style={{ margin: 0 }}>
            <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>Description</label>
            <textarea
              className="input-field"
              value={editOrgData.description}
              onChange={e => setEditOrgData({ ...editOrgData, description: e.target.value })}
              rows={4}
              style={{ marginTop: '0.35rem' }}
            />
          </div>
          <button type="submit" className="btn-primary" style={{ width: 'auto', padding: '0.65rem 1.75rem', fontSize: '0.85rem', alignSelf: 'flex-start' }} disabled={loading}>
            {loading ? <Loader2 className="animate-spin" /> : 'Save Workspace Info'}
          </button>
        </form>
      </div>
      {selectedOrg?.my_status?.role === 'owner' && (
        <div className="workspace-management-card">
          <div className="workspace-management-header">
            <AlertCircle size={20} color="#ef4444" />
            <h3 className="workspace-management-title">Workspace Management</h3>
          </div>
          <div className="workspace-management-row">
            <div className="workspace-management-info">
              <h4 className="workspace-management-action-title">Deactivate Workspace</h4>
              <p className="workspace-management-desc">
                Temporarily hide this workspace from all members and pause operations.
              </p>
              <ul className="workspace-management-impact-list">
                <li>The workspace will be hidden from members' lists.</li>
                <li>All tasks, goals, templates, and chats will be archived.</li>
                <li>Workspace data is safe and can be reactivated by the owner at any time.</li>
              </ul>
            </div>
            <button
              type="button"
              className="btn-deactivate-premium"
              onClick={() => {
                setView('deactivate-workspace');
                setConfirmInput('');
                setConfirmModalError('');
              }}
              disabled={loading}
            >
              Deactivate Workspace
            </button>
          </div>
          <div className="workspace-management-row">
            <div className="workspace-management-info">
              <h4 className="workspace-management-action-title" style={{ color: '#ef4444' }}>Permanently Delete Workspace</h4>
              <p className="workspace-management-desc">
                Completely wipe all data associated with this workspace. This action is irreversible.
              </p>
              <ul className="workspace-management-impact-list" style={{ color: '#b91c1c' }}>
                <li>All members will instantly lose access.</li>
                <li>All tasks, chat history, attachments, goals, and notes will be permanently deleted.</li>
                <li>This database volume cannot be restored.</li>
              </ul>
            </div>
            <button
              type="button"
              className="btn-delete-premium"
              onClick={() => {
                setView('delete-workspace');
                setConfirmInput('');
                setConfirmModalError('');
              }}
              disabled={loading}
            >
              Delete Workspace
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
{
  activeTab === 'leaves' && (
    <div className="leaves-view" style={{ maxWidth: '1000px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem', padding: '0.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #e2e8f0', paddingBottom: '1rem' }}>
        <div>
          <h2 className="section-title-premium" style={{ margin: 0 }}>Leave Management</h2>
          <p className="section-subtitle-premium" style={{ margin: '0.25rem 0 0 0' }}>
            Apply for leave, track leave history, or manage team leave requests.
          </p>
        </div>
        {(selectedOrg?.my_status?.role === 'owner' || selectedOrg?.my_status?.role === 'admin') && (
          <div style={{ display: 'flex', background: '#f1f5f9', borderRadius: '8px', padding: '0.25rem' }}>
            <button
              onClick={() => setLeavesViewTab('my-leaves')}
              style={{
                padding: '0.5rem 1rem',
                borderRadius: '6px',
                border: 'none',
                background: leavesViewTab === 'my-leaves' ? '#ffffff' : 'transparent',
                color: leavesViewTab === 'my-leaves' ? '#4f46e5' : '#64748b',
                fontWeight: 600,
                cursor: 'pointer',
                boxShadow: leavesViewTab === 'my-leaves' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                transition: 'all 0.2s'
              }}
            >
              My Leaves
            </button>
            <button
              onClick={() => setLeavesViewTab('team-leaves')}
              style={{
                padding: '0.5rem 1rem',
                borderRadius: '6px',
                border: 'none',
                background: leavesViewTab === 'team-leaves' ? '#ffffff' : 'transparent',
                color: leavesViewTab === 'team-leaves' ? '#4f46e5' : '#64748b',
                fontWeight: 600,
                cursor: 'pointer',
                boxShadow: leavesViewTab === 'team-leaves' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                transition: 'all 0.2s'
              }}
            >
              Team Requests
            </button>
          </div>
        )}
      </div>
      {leaveError && <div className="error-message" style={{ marginBottom: '0.5rem' }}>{leaveError}</div>}
      {leaveSuccess && <div className="success-message" style={{ marginBottom: '0.5rem' }}>{leaveSuccess}</div>}
      {leavesViewTab === 'my-leaves' ? (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: '1.5rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {/* Leave Balances */}
            <div className="premium-card-settings" style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '1.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
              <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', fontWeight: 600, color: '#1e293b' }}>Leave Balances</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {leaveBalances.length === 0 ? (
                  <p style={{ margin: 0, fontSize: '0.85rem', color: '#64748b' }}>No balances tracked yet.</p>
                ) : (
                  leaveBalances.map(balance => (
                    <div key={balance.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem', background: '#f8fafc', borderRadius: '6px' }}>
                      <span style={{ fontSize: '0.85rem', fontWeight: 500, color: '#334155' }}>{balance.leave_type_display}</span>
                      <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#4f46e5' }}>{balance.remaining_days} days left</span>
                    </div>
                  ))
                )}
              </div>
            </div>
            {/* Apply Form */}
            <div className="premium-card-settings" style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '1.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.05)', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem', fontWeight: 600, color: '#1e293b' }}>Apply for Leave</h3>
            <form onSubmit={handleApplyLeave} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div className="input-group" style={{ margin: 0 }}>
                <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>Leave Type</label>
                <select
                  value={leaveForm.leave_type}
                  onChange={(e) => setLeaveForm({ ...leaveForm, leave_type: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '0.65rem 0.85rem',
                    borderRadius: '8px',
                    border: '1px solid #cbd5e1',
                    marginTop: '0.35rem',
                    background: '#ffffff',
                    fontSize: '0.9rem'
                  }}
                >
                  <option value="Sick">Sick Leave</option>
                  <option value="Casual">Casual Leave</option>
                  <option value="Earned">Earned Leave</option>
                  <option value="WFH">Work From Home</option>
                  <option value="Half_Day">Half Day</option>
                  <option value="Comp_Off">Comp Off</option>
                  <option value="Optional">Optional Leave</option>
                  <option value="Maternity_Paternity">Maternity/Paternity Leave</option>
                  <option value="Annual">Annual Leave</option>
                  <option value="Unpaid">Unpaid Leave</option>
                </select>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="input-group" style={{ margin: 0 }}>
                  <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>Start Date</label>
                  <input
                    type="date"
                    required
                    value={leaveForm.start_date}
                    onChange={(e) => setLeaveForm({ ...leaveForm, start_date: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '0.65rem 0.85rem',
                      borderRadius: '8px',
                      border: '1px solid #cbd5e1',
                      marginTop: '0.35rem',
                      fontSize: '0.9rem'
                    }}
                  />
                </div>
                <div className="input-group" style={{ margin: 0 }}>
                  <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>End Date</label>
                  <input
                    type="date"
                    required
                    value={leaveForm.end_date}
                    onChange={(e) => setLeaveForm({ ...leaveForm, end_date: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '0.65rem 0.85rem',
                      borderRadius: '8px',
                      border: '1px solid #cbd5e1',
                      marginTop: '0.35rem',
                      fontSize: '0.9rem'
                    }}
                  />
                </div>
              </div>
              <div className="input-group" style={{ margin: 0 }}>
                <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>Reason</label>
                <textarea
                  required
                  rows="4"
                  placeholder="Please explain the reason for your leave request..."
                  value={leaveForm.reason}
                  onChange={(e) => setLeaveForm({ ...leaveForm, reason: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '0.65rem 0.85rem',
                    borderRadius: '8px',
                    border: '1px solid #cbd5e1',
                    marginTop: '0.35rem',
                    fontSize: '0.9rem',
                    resize: 'vertical'
                  }}
                />
              </div>
              <div className="input-group" style={{ margin: 0 }}>
                <label className="input-label" style={{ fontWeight: 600, color: '#334155', fontSize: '0.85rem' }}>Supporting Document (Optional)</label>
                <input
                  type="file"
                  onChange={(e) => setLeaveForm({ ...leaveForm, attachment: e.target.files[0] })}
                  style={{
                    width: '100%',
                    padding: '0.65rem 0.85rem',
                    borderRadius: '8px',
                    border: '1px solid #cbd5e1',
                    marginTop: '0.35rem',
                    fontSize: '0.9rem',
                    background: '#ffffff'
                  }}
                />
              </div>
              <button
                type="submit"
                className="btn-premium-action"
                disabled={leaveLoading}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  borderRadius: '8px',
                  background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
                  color: '#ffffff',
                  fontWeight: 600,
                  border: 'none',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  transition: 'all 0.2s',
                  opacity: leaveLoading ? 0.7 : 1
                }}
              >
                {leaveLoading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Submitting...
                  </>
                ) : 'Submit Request'}
              </button>
            </form>
          </div>
          </div>
          {/* Leave History */}
          <div className="premium-card-settings" style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '1.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.05)', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem', fontWeight: 600, color: '#1e293b' }}>My Leave History</h3>
            {userLeaves.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '3rem 1rem', color: '#64748b' }}>
                <Coffee size={32} style={{ color: '#cbd5e1', marginBottom: '0.75rem' }} />
                <p style={{ margin: 0, fontSize: '0.95rem' }}>No leave requests found.</p>
                <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.8rem' }}>Your submitted leave requests will appear here.</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', overflowY: 'auto', maxHeight: '450px' }}>
                {userLeaves.map((leave) => {
                  const statusColor =
                    leave.status === 'Approved' ? { bg: '#d1fae5', text: '#065f46' } :
                      leave.status === 'Rejected' ? { bg: '#fee2e2', text: '#991b1b' } :
                        { bg: '#fef3c7', text: '#92400e' };
                  return (
                    <div key={leave.id} style={{ border: '1px solid #e2e8f0', borderRadius: '8px', padding: '1rem', background: '#f8fafc', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: 600, fontSize: '0.9rem', color: '#1e293b' }}>
                          {leave.leave_type} Leave
                        </span>
                        <span style={{
                          backgroundColor: statusColor.bg,
                          color: statusColor.text,
                          padding: '0.15rem 0.5rem',
                          borderRadius: '4px',
                          fontSize: '0.75rem',
                          fontWeight: 'bold'
                        }}>
                          {leave.status}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                        <strong>Period:</strong> {new Date(leave.start_date).toLocaleDateString()} to {new Date(leave.end_date).toLocaleDateString()}
                      </div>
                      <div style={{ fontSize: '0.85rem', color: '#475569', borderLeft: '3px solid #cbd5e1', paddingLeft: '0.5rem', margin: '0.25rem 0 0 0' }}>
                        {leave.reason}
                      </div>
                      {leave.attachment && (
                        <div style={{ fontSize: '0.8rem', color: '#4f46e5', marginTop: '0.25rem' }}>
                          <a href={leave.attachment} target="_blank" rel="noopener noreferrer">View Attachment</a>
                        </div>
                      )}
                      {leave.status === 'Rejected' && leave.rejection_reason && (
                        <div style={{ fontSize: '0.85rem', color: '#991b1b', background: '#fee2e2', padding: '0.5rem', borderRadius: '4px', marginTop: '0.5rem' }}>
                          <strong>Rejection Reason:</strong> {leave.rejection_reason}
                        </div>
                      )}
                      {leave.status === 'Cancelled' && leave.cancellation_reason && (
                        <div style={{ fontSize: '0.85rem', color: '#92400e', background: '#fef3c7', padding: '0.5rem', borderRadius: '4px', marginTop: '0.5rem' }}>
                          <strong>Cancellation Reason:</strong> {leave.cancellation_reason}
                        </div>
                      )}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.25rem' }}>
                        {leave.approved_by_details && (
                          <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                            Reviewed by: {leave.approved_by_details.email}
                          </div>
                        )}
                        {(leave.status === 'Pending' || leave.status === 'Approved') && (
                          <button
                            onClick={(e) => { e.preventDefault(); handleCancelLeave(leave.id); }}
                            disabled={leaveLoading}
                            style={{
                              padding: '0.25rem 0.5rem',
                              fontSize: '0.75rem',
                              borderRadius: '4px',
                              background: '#fee2e2',
                              color: '#b91c1c',
                              border: 'none',
                              cursor: 'pointer',
                              marginLeft: 'auto'
                            }}
                          >
                            Cancel Leave
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Team Leaves Board for managers */
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '1.5rem' }}>
          {/* Pending Board */}
          <div className="premium-card-settings" style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '1.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.05)', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem', fontWeight: 600, color: '#1e293b' }}>Pending Approvals</h3>
            {allLeaves.filter(l => l.status === 'Pending').length === 0 ? (
              <div style={{ textAlign: 'center', padding: '3rem 1rem', color: '#64748b' }}>
                <CheckCircle2 size={32} style={{ color: '#10b981', marginBottom: '0.75rem' }} />
                <p style={{ margin: 0, fontSize: '0.95rem', fontWeight: 600 }}>All caught up!</p>
                <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.8rem' }}>No pending leave requests to review.</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', overflowY: 'auto', maxHeight: '450px' }}>
                {allLeaves.filter(l => l.status === 'Pending').map((leave) => (
                  <div key={leave.id} style={{ border: '1px solid #e2e8f0', borderRadius: '8px', padding: '1rem', background: '#f8fafc', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#1e293b' }}>
                          {leave.user_details?.email}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.1rem' }}>
                          Requested <strong>{leave.leave_type}</strong> leave
                        </div>
                      </div>
                      <span style={{
                        backgroundColor: '#fef3c7',
                        color: '#92400e',
                        padding: '0.15rem 0.5rem',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        fontWeight: 'bold'
                      }}>
                        Pending
                      </span>
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                      <strong>Period:</strong> {new Date(leave.start_date).toLocaleDateString()} to {new Date(leave.end_date).toLocaleDateString()}
                    </div>
                    <div style={{ fontSize: '0.85rem', color: '#475569', borderLeft: '3px solid #cbd5e1', paddingLeft: '0.5rem', margin: '0.25rem 0' }}>
                      {leave.reason}
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem', justifyContent: 'flex-end' }}>
                      <button
                        onClick={() => handleRejectLeave(leave.id)}
                        disabled={leaveLoading}
                        style={{
                          padding: '0.4rem 0.8rem',
                          borderRadius: '6px',
                          background: '#fee2e2',
                          color: '#b91c1c',
                          border: 'none',
                          fontWeight: 600,
                          fontSize: '0.8rem',
                          cursor: 'pointer',
                          transition: 'all 0.2s',
                          boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
                        }}
                        onMouseEnter={(e) => e.target.style.background = '#fca5a5'}
                        onMouseLeave={(e) => e.target.style.background = '#fee2e2'}
                      >
                        Reject
                      </button>
                      <button
                        onClick={() => handleApproveLeave(leave.id)}
                        disabled={leaveLoading}
                        style={{
                          padding: '0.4rem 0.8rem',
                          borderRadius: '6px',
                          background: '#d1fae5',
                          color: '#065f46',
                          border: 'none',
                          fontWeight: 600,
                          fontSize: '0.8rem',
                          cursor: 'pointer',
                          transition: 'all 0.2s',
                          boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
                        }}
                        onMouseEnter={(e) => e.target.style.background = '#a7f3d0'}
                        onMouseLeave={(e) => e.target.style.background = '#d1fae5'}
                      >
                        Approve
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          {/* Team Review History */}
          <div className="premium-card-settings" style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '1.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.05)', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem', fontWeight: 600, color: '#1e293b' }}>Decision History</h3>
            {allLeaves.filter(l => l.status !== 'Pending').length === 0 ? (
              <div style={{ textAlign: 'center', padding: '3rem 1rem', color: '#64748b' }}>
                <History size={32} style={{ color: '#cbd5e1', marginBottom: '0.75rem' }} />
                <p style={{ margin: 0, fontSize: '0.95rem' }}>No history records.</p>
                <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.8rem' }}>Decisions will be archived here.</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', overflowY: 'auto', maxHeight: '450px' }}>
                {allLeaves.filter(l => l.status !== 'Pending').map((leave) => {
                  const statusColor =
                    leave.status === 'Approved' ? { bg: '#d1fae5', text: '#065f46' } :
                      { bg: '#fee2e2', text: '#991b1b' };
                  return (
                    <div key={leave.id} style={{ border: '1px solid #e2e8f0', borderRadius: '8px', padding: '1rem', background: '#f8fafc', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: 600, fontSize: '0.85rem', color: '#1e293b' }}>
                          {leave.user_details?.email}
                        </span>
                        <span style={{
                          backgroundColor: statusColor.bg,
                          color: statusColor.text,
                          padding: '0.1rem 0.4rem',
                          borderRadius: '4px',
                          fontSize: '0.7rem',
                          fontWeight: 'bold'
                        }}>
                          {leave.status}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                        {leave.leave_type} leave from {new Date(leave.start_date).toLocaleDateString()} to {new Date(leave.end_date).toLocaleDateString()}
                      </div>
                      {leave.approved_by_details && (
                        <div style={{ fontSize: '0.7rem', color: '#94a3b8', textAlign: 'right', marginTop: '0.25rem' }}>
                          Reviewed by: {leave.approved_by_details.email}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
          </div >
        </main >
  { showInviteModal && (
    <div className="modal-overlay" onClick={() => { setShowInviteModal(false); setShowRoleDropdown(false); }}>
      <div className="modal-card invite-premium-modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '440px', padding: '1.75rem', borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)', background: '#ffffff', position: 'relative' }}>
        {/* Close Button */}
        <button
          type="button"
          className="invite-close-btn"
          onClick={() => { setShowInviteModal(false); setShowRoleDropdown(false); }}
          title="Close"
          style={{ position: 'absolute', right: '1.25rem', top: '1.25rem', border: 'none', background: 'transparent', fontSize: '1.5rem', fontWeight: '300', color: '#94a3b8', cursor: 'pointer', transition: 'color 0.2s' }}
          onMouseEnter={(e) => e.target.style.color = '#475569'}
          onMouseLeave={(e) => e.target.style.color = '#94a3b8'}
        >
          &times;
        </button>
        <div className="modal-header" style={{ paddingBottom: '0.75rem', borderBottom: '1px solid #f1f5f9', marginBottom: '1.25rem' }}>
          <h2 className="modal-title" style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.15rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>Invite people for free</h2>
        </div>
        <form onSubmit={handleSendInvite}>
          {/* Invite by email Input */}
          <div className="input-group" style={{ marginBottom: '1.25rem' }}>
            <label className="input-label" style={{ fontWeight: 600, fontSize: '0.7rem', color: '#475569', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem', display: 'block' }}>Invite by email</label>
            <input
              className="input-field invite-premium-input"
              type="text"
              placeholder="Email, comma or space separated"
              value={inviteData.email}
              onChange={e => setInviteData({ ...inviteData, email: e.target.value })}
              required
              style={{ width: '100%', borderRadius: '8px', padding: '0.65rem 0.85rem', fontSize: '0.85rem', border: '1px solid #cbd5e1', outline: 'none' }}
            />
          </div>
          {/* Invite as Dropdown */}
          <div className="input-group" style={{ position: 'relative', marginBottom: '1.25rem' }}>
            <label className="input-label" style={{ fontWeight: 600, fontSize: '0.7rem', color: '#475569', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem', display: 'block' }}>Invite as</label>
            {/* Select Box Container */}
            <div
              className="invite-role-select-box"
              onClick={() => setShowRoleDropdown(!showRoleDropdown)}
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #cbd5e1', cursor: 'pointer', background: '#ffffff', transition: 'border-color 0.2s' }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div className="invite-role-avatar" style={{ width: '28px', height: '28px', borderRadius: '50%', background: '#f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Users size={13} style={{ color: '#475569' }} />
                </div>
                <div style={{ textAlign: 'left' }}>
                  <div className="invite-role-title" style={{ fontSize: '0.85rem', fontWeight: 600, color: '#0f172a' }}>
                    {inviteData.role === 'admin' ? 'Admin' :
                      inviteData.role === 'limited_member' ? 'Limited Member' :
                        inviteData.role === 'guest' ? 'Guest' : 'Member'}
                  </div>
                  <div className="invite-role-desc" style={{ fontSize: '0.75rem', color: '#64748b', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '240px', marginTop: '1px' }}>
                    {inviteData.role === 'admin' && 'Can manage Spaces, People, Billing and other Workspace settings.'}
                    {inviteData.role === 'limited_member' && 'Can only access items shared with them.'}
                    {inviteData.role === 'guest' && "Can't use all features or be added to Spaces. Can only access items shared with them."}
                    {inviteData.role === 'member' && 'Can access all public items in your Workspace.'}
                  </div>
                </div>
              </div>
              <span className="invite-role-chevron" style={{ fontSize: '0.65rem', color: '#94a3b8' }}>{showRoleDropdown ? '▲' : '▼'}</span>
            </div>
            {/* Dropdown Menu Overlay */}
            {showRoleDropdown && (
              <div className="invite-role-dropdown-menu" style={{ position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 100, marginTop: '0.5rem', background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)', padding: '0.5rem 0', overflow: 'hidden' }}>
                {/* Member option */}
                <div
                  className={`invite-role-option ${inviteData.role === 'member' ? 'selected' : ''}`}
                  onClick={() => { setInviteData({ ...inviteData, role: 'member' }); setShowRoleDropdown(false); }}
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.6rem 1rem', cursor: 'pointer', borderLeft: inviteData.role === 'member' ? '3px solid #6366f1' : '3px solid transparent', background: inviteData.role === 'member' ? '#f8fafc' : 'transparent' }}
                >
                  <div className="invite-option-content" style={{ textAlign: 'left' }}>
                    <span className="invite-option-title" style={{ fontSize: '0.825rem', fontWeight: 600, color: '#1e293b' }}>Member</span>
                    <div className="invite-option-desc" style={{ fontSize: '0.725rem', color: '#64748b', marginTop: '2px' }}>Can access all public items in your Workspace.</div>
                  </div>
                  {inviteData.role === 'member' && <span className="invite-option-checkmark" style={{ color: '#6366f1', fontSize: '0.85rem', fontWeight: 'bold' }}>✓</span>}
                </div>
                {/* Limited Member option */}
                <div
                  className={`invite-role-option ${inviteData.role === 'limited_member' ? 'selected' : ''}`}
                  onClick={() => { setInviteData({ ...inviteData, role: 'limited_member' }); setShowRoleDropdown(false); }}
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.6rem 1rem', cursor: 'pointer', borderLeft: inviteData.role === 'limited_member' ? '3px solid #6366f1' : '3px solid transparent', background: inviteData.role === 'limited_member' ? '#f8fafc' : 'transparent' }}
                >
                  <div className="invite-option-content" style={{ textAlign: 'left' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span className="invite-option-title" style={{ fontSize: '0.825rem', fontWeight: 600, color: '#1e293b' }}>Limited Member</span>
                      <span className="invite-option-badge" style={{ fontSize: '0.65rem', background: '#faf5ff', color: '#8b5cf6', border: '1px solid #ebd5ff', padding: '0.05rem 0.35rem', borderRadius: '4px', fontWeight: 500 }}>Chat Collaborator</span>
                    </div>
                    <div className="invite-option-desc" style={{ fontSize: '0.725rem', color: '#64748b', marginTop: '2px' }}>Can only access items shared with them.</div>
                  </div>
                  {inviteData.role === 'limited_member' && <span className="invite-option-checkmark" style={{ color: '#6366f1', fontSize: '0.85rem', fontWeight: 'bold' }}>✓</span>}
                </div>
                {/* Guest option */}
                <div
                  className={`invite-role-option ${inviteData.role === 'guest' ? 'selected' : ''}`}
                  onClick={() => { setInviteData({ ...inviteData, role: 'guest' }); setShowRoleDropdown(false); }}
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.6rem 1rem', cursor: 'pointer', borderLeft: inviteData.role === 'guest' ? '3px solid #6366f1' : '3px solid transparent', background: inviteData.role === 'guest' ? '#f8fafc' : 'transparent' }}
                >
                  <div className="invite-option-content" style={{ textAlign: 'left' }}>
                    <span className="invite-option-title" style={{ fontSize: '0.825rem', fontWeight: 600, color: '#1e293b' }}>Guest</span>
                    <div className="invite-option-desc" style={{ fontSize: '0.725rem', color: '#64748b', marginTop: '2px' }}>Can't use all features or be added to Spaces. Can only access items shared with them.</div>
                  </div>
                  {inviteData.role === 'guest' && <span className="invite-option-checkmark" style={{ color: '#6366f1', fontSize: '0.85rem', fontWeight: 'bold' }}>✓</span>}
                </div>
                {/* Admin option */}
                <div
                  className={`invite-role-option ${inviteData.role === 'admin' ? 'selected' : ''}`}
                  onClick={() => { setInviteData({ ...inviteData, role: 'admin' }); setShowRoleDropdown(false); }}
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.6rem 1rem', cursor: 'pointer', borderLeft: inviteData.role === 'admin' ? '3px solid #6366f1' : '3px solid transparent', background: inviteData.role === 'admin' ? '#f8fafc' : 'transparent' }}
                >
                  <div className="invite-option-content" style={{ textAlign: 'left' }}>
                    <span className="invite-option-title" style={{ fontSize: '0.825rem', fontWeight: 600, color: '#1e293b' }}>Admin</span>
                    <div className="invite-option-desc" style={{ fontSize: '0.725rem', color: '#64748b', marginTop: '2px' }}>Can manage Spaces, People, Billing and other Workspace settings.</div>
                  </div>
                  {inviteData.role === 'admin' && <span className="invite-option-checkmark" style={{ color: '#6366f1', fontSize: '0.85rem', fontWeight: 'bold' }}>✓</span>}
                </div>
                <div className="invite-dropdown-divider" style={{ height: '1px', background: '#f1f5f9', margin: '0.4rem 0' }}></div>
                {/* Add Custom Role */}
                <div className="invite-role-option-custom" style={{ padding: '0.5rem 1rem', textAlign: 'left', color: '#94a3b8', fontSize: '0.8rem', cursor: 'not-allowed', fontStyle: 'italic' }}>
                  <span>+ Add custom role</span>
                </div>
              </div>
            )}
          </div>
          {/* Message Input */}
          <div className="input-group" style={{ marginBottom: '1.25rem' }}>
            <label className="input-label" style={{ fontWeight: 600, fontSize: '0.7rem', color: '#475569', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem', display: 'block' }}>Message (Optional)</label>
            <textarea
              className="input-field invite-premium-input"
              placeholder="Add a personalized message..."
              value={inviteData.message}
              onChange={e => setInviteData({ ...inviteData, message: e.target.value })}
              style={{ width: '100%', borderRadius: '8px', padding: '0.65rem 0.85rem', fontSize: '0.85rem', border: '1px solid #cbd5e1', outline: 'none', minHeight: '80px', resize: 'vertical' }}
            />
          </div>
          <div className="modal-footer" style={{ borderTop: 'none', padding: '0.5rem 0 0 0', display: 'flex', justifyContent: 'flex-end', marginTop: '1.25rem' }}>
            <button
              type="submit"
              className="invite-send-btn"
              disabled={loading}
              style={{ background: '#0f172a', color: '#ffffff', border: 'none', borderRadius: '24px', padding: '0.6rem 1.4rem', fontSize: '0.85rem', fontWeight: 600, cursor: 'pointer', transition: 'background-color 0.2s', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
              onMouseEnter={(e) => e.target.style.background = '#1e293b'}
              onMouseLeave={(e) => e.target.style.background = '#0f172a'}
            >
              {loading ? <Loader2 className="animate-spin" size={14} /> : 'Send free invite'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )}
{/* Floating Note Action Button */ }
<div
  className="floating-note-btn"
  onClick={() => { setShowNotebook(!showNotebook); if (!activeNote && notes.length > 0) { setActiveNote(notes[0]); setNoteTitle(notes[0].title); setNoteContent(notes[0].content); } }}
  title="Quick Notes"
>
  <Edit3 size={20} />
</div>
{/* Quick Notes Side-Drawer Panel */ }
{
  showNotebook && (
    <div className="notes-drawer-overlay" onClick={() => setShowNotebook(false)}>
      <div className="notes-drawer" onClick={(e) => e.stopPropagation()}>
        <div className="notes-drawer-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <BookOpen size={18} style={{ color: '#6366f1' }} />
            <span className="notes-drawer-title">Workspace Notebook</span>
          </div>
          <button className="notes-drawer-close" onClick={() => setShowNotebook(false)}>&times;</button>
        </div>
        <div className="notes-drawer-body">
          {/* Notes List Column */}
          <div className="notes-list-pane" style={{ width: `${notesSidebarWidth}px`, flexShrink: 0 }}>
            <button className="new-note-btn" onClick={handleCreateNote} disabled={savingNote}>
              <Plus size={14} /> New Note
            </button>
            <div className="notes-list-scroll">
              {notes.length === 0 ? (
                <div className="empty-notes-prompt">
                  <StickyNote size={24} style={{ color: '#cbd5e1', marginBottom: '0.5rem' }} />
                  <span>No notes yet. Create one!</span>
                </div>
              ) : (
                notes.map(note => (
                  <div
                    key={note.id}
                    className={`note-list-item ${activeNote?.id === note.id ? 'active' : ''}`}
                    onClick={() => {
                      setActiveNote(note);
                      setNoteTitle(note.title);
                      setNoteContent(note.content);
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                      <span className="note-list-title">{note.title || 'Untitled Note'}</span>
                      <button className="note-delete-btn" onClick={(e) => handleDeleteNote(note.id, e)}>
                        <Trash2 size={12} />
                      </button>
                    </div>
                    <span className="note-list-date">{new Date(note.updated_at).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                ))
              )}
            </div>
          </div>
          {/* Resize Handle */}
          <div
            onMouseDown={handleNotesSidebarResize}
            style={{
              width: '6px',
              cursor: 'col-resize',
              alignSelf: 'stretch',
              background: '#e2e8f0',
              margin: '0 -3px',
              zIndex: 10,
              transition: 'background 0.2s',
              borderRadius: '3px',
              flexShrink: 0
            }}
            onMouseEnter={(e) => e.target.style.background = '#6366f1'}
            onMouseLeave={(e) => e.target.style.background = '#e2e8f0'}
          />
          {/* Note Editor Column */}
          <div className="note-editor-pane">
            {activeNote ? (
              <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <input
                    type="text"
                    className="note-title-input"
                    placeholder="Note Title"
                    value={noteTitle}
                    onChange={(e) => {
                      setNoteTitle(e.target.value);
                    }}
                    onBlur={() => handleUpdateNote(noteTitle, noteContent)}
                  />
                  <button
                    className="note-save-btn"
                    onClick={() => handleUpdateNote(noteTitle, noteContent)}
                    disabled={savingNote}
                  >
                    {savingNote ? 'Saving...' : 'Save'}
                  </button>
                </div>
                <textarea
                  className="note-content-textarea"
                  placeholder="Write something beautiful..."
                  value={noteContent}
                  onChange={(e) => {
                    setNoteContent(e.target.value);
                  }}
                  onBlur={() => handleUpdateNote(noteTitle, noteContent)}
                />
              </div>
            ) : (
              <div className="editor-empty-state">
                <BookOpen size={48} style={{ color: '#cbd5e1', marginBottom: '1rem' }} />
                <p style={{ fontWeight: 600, color: '#64748b' }}>No Note Selected</p>
                <p style={{ fontSize: '0.8rem', color: '#94a3b8', textAlign: 'center' }}>Select a note from the left sidebar or create a new one to start writing!</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
        <SharingSettingsModal 
          isOpen={sharingModalConfig.isOpen} 
          onClose={closeSharingModal} 
          data={sharingModalConfig.data || {}} 
          onChange={handleSharingModalChange}
          members={orgMembers}
        />
        <TaskFeedbackModal 
          isOpen={feedbackModalConfig.isOpen}
          onClose={() => setFeedbackModalConfig({ isOpen: false, taskId: null, taskTitle: '' })}
          taskId={feedbackModalConfig.taskId}
          taskTitle={feedbackModalConfig.taskTitle}
        />
        <TaskExtensionModal
          isOpen={extensionModalConfig.isOpen}
          onClose={() => setExtensionModalConfig({ isOpen: false, taskId: null, taskTitle: '', currentDueDate: null })}
          taskId={extensionModalConfig.taskId}
          taskTitle={extensionModalConfig.taskTitle}
          currentDueDate={extensionModalConfig.currentDueDate}
        />
        <ExtensionRequestsModal
          isOpen={isExtensionRequestsModalOpen}
          onClose={() => setIsExtensionRequestsModalOpen(false)}
          orgId={selectedOrg?.id}
        />

{/* Commented: Smart Suggestion Feature
        <CheckFreeMembersModal
          isOpen={isFreeMembersModalOpen}
          onClose={() => setIsFreeMembersModalOpen(false)}
          selectedOrg={selectedOrg}
          orgMembers={orgMembers}
          handleLoadTasks={handleLoadTasks}
        />
        */}
{
  workloadLimitWarning && (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(15, 23, 42, 0.4)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: '1rem'
    }}>
      <div style={{
        backgroundColor: '#ffffff',
        borderRadius: '16px',
        width: '100%',
        maxWidth: '440px',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        border: '1px solid #f1f5f9',
        overflow: 'hidden'
      }}>
        <div style={{ height: '6px', background: 'linear-gradient(90deg, #ea580c 0%, #ef4444 100%)' }} />
        <div style={{ padding: '1.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
            <div style={{
              backgroundColor: '#fff7ed',
              border: '1px solid #ffedd5',
              borderRadius: '12px',
              padding: '0.75rem',
              color: '#ea580c',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}>
              <AlertCircle size={24} />
            </div>
            <div style={{ flex: 1 }}>
              <h3 style={{
                fontSize: '1.125rem',
                fontWeight: 700,
                color: '#0f172a',
                margin: '0 0 0.5rem 0'
              }}>
                Task Limit Active
              </h3>
              <p style={{
                fontSize: '0.875rem',
                color: '#475569',
                lineHeight: '1.5',
                margin: 0
              }}>
                {workloadLimitWarning}
              </p>
            </div>
          </div>
        </div>
        <div style={{
          backgroundColor: '#f8fafc',
          padding: '1rem 1.75rem',
          borderTop: '1px solid #f1f5f9',
          display: 'flex',
          justifyContent: 'flex-end',
          gap: '0.75rem'
        }}>
          <button
            onClick={() => setWorkloadLimitWarning(null)}
            style={{
              backgroundColor: '#0f172a',
              color: '#ffffff',
              border: 'none',
              borderRadius: '8px',
              padding: '0.5rem 1.25rem',
              fontSize: '0.875rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            Okay, I'll Complete It
          </button>
        </div>
      </div>
    </div>
  )
}
      </div >
    );
  }
if (view === 'connecting_sso') {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      width: '100vw',
      background: '#0f172a',
      color: 'white',
      fontFamily: 'Inter, sans-serif'
    }}>
      <Loader2 className="animate-spin" size={48} style={{ color: '#6366f1', marginBottom: '1rem' }} />
      <h2 style={{ fontSize: '1.25rem', fontWeight: 500, letterSpacing: '1px' }}>Completing Single Sign-On...</h2>
      <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginTop: '0.5rem' }}>We are logging you in securely. Please wait.</p>
    </div>
  );
}
if (view === 'initializing') {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      width: '100vw',
      background: '#0f172a',
      color: 'white',
      fontFamily: 'Inter, sans-serif'
    }}>
      <Loader2 className="animate-spin" size={48} style={{ color: '#6366f1', marginBottom: '1rem' }} />
      <h2 style={{ fontSize: '1.25rem', fontWeight: 500, letterSpacing: '1px' }}>Loading ParseOps...</h2>
    </div>
  );
}
if (view === 'force_password_change') {
  return (
    <div className="auth-container">
      <div className="auth-left">
        <div className="auth-card">
          <div className="logo-container">
            <Lock size={32} color="#6366f1" />
          </div>
          <h1 className="form-title" style={{ fontSize: '1.5rem' }}>Change Your Password</h1>
          <p className="form-subtitle">For your security, please create a new password before continuing.</p>
          {error && <div className="error-message">{error}</div>}
          {message && <div className="success-message">{message}</div>}
          <form onSubmit={async (e) => {
            e.preventDefault();
            setLoading(true);
            setError('');
            try {
              await changePassword(formData.email, formData.password);
              setMessage('Password updated successfully!');
              await fetchWorkspaces(sessionStorage.getItem('access_token'));
            } catch (err) {
              setError(err.response?.data?.error || err.response?.data?.detail || 'Failed to update password');
            } finally {
              setLoading(false);
            }
          }}>
            <div className="input-group">
              <label>Email Address</label>
              <div className="input-wrapper">
                <input type="email" value={formData.email} disabled className="input-field" style={{ backgroundColor: '#f1f5f9' }} />
              </div>
            </div>
            <div className="input-group">
              <label>New Password</label>
              <div className="input-wrapper">
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  className="input-field"
                  value={formData.password}
                  onChange={e => setFormData({ ...formData, password: e.target.value })}
                />
                <button type="button" className="password-toggle" onClick={() => setShowPassword(!showPassword)}>
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>
            <button type="submit" className="btn-primary" disabled={loading} style={{ marginTop: '1rem' }}>
              {loading ? <Loader2 className="animate-spin" /> : 'Update Password & Continue'}
            </button>
          </form>
        </div>
      </div>
      <div className="auth-right">
        <div className="auth-right-content">
          <h2 className="auth-quote">"Security is not a product, but a process."</h2>
          <p className="auth-author">- Bruce Schneier</p>
        </div>
      </div>
    </div>
  );
}
if (view === 'verify') {
  return (
    <div className="verify-container">
      <div className="verify-card">
        <div className="hero-icon"><Mail size={32} color="white" /></div>
        <h1 className="form-title">Verify Your Email</h1>
        <p className="form-subtitle">We've sent a 6-digit OTP to your email</p>
        <div className="email-badge">{formData.email}</div>
        <form onSubmit={handleAuthAction}>
          <div className="otp-grid">
            {otp.map((digit, i) => (
              <input
                key={i}
                ref={el => otpRefs.current[i] = el}
                className="otp-input"
                type="text"
                inputMode="numeric"
                autoComplete={i === 0 ? "one-time-code" : "off"}
                maxLength={i === 0 ? "6" : "1"}
                value={digit}
                onChange={e => handleOtpChange(i, e.target.value)}
                onKeyDown={e => handleKeyDown(i, e)}
                onPaste={i === 0 ? handlePaste : undefined}
              />
            ))}
          </div>
          {purpose === 'password_reset' && (
            <div className="input-group" style={{ textAlign: 'left' }}>
              <label className="input-label">New Password</label>
              <div className="password-wrapper">
                <input
                  className="input-field"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter new password"
                  value={formData.password}
                  onChange={e => setFormData({ ...formData, password: e.target.value })}
                  required
                />
                <button type="button" className="eye-btn" onClick={() => setShowPassword(!showPassword)}>
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>
          )}
          {error && <div className="error-message">{error}</div>}
          {message && <div className="success-message">{message}</div>}
          <button type="submit" className="btn-primary" disabled={loading || otp.join('').length < 6}>
            {loading ? <Loader2 className="animate-spin" /> : purpose === 'password_reset' ? 'Update Password' : 'Verify OTP'}
          </button>
        </form>
        <p className="signup-link" style={{ marginTop: '2rem' }}>
          Didn't receive it? <a href="#" onClick={handleResend}>Resend OTP</a>
        </p>
        <button className="social-btn" onClick={() => setView('login')} style={{ border: 'none', background: 'none', color: '#64748b', fontSize: '0.9rem' }}>
          <ArrowLeft size={16} /> Back to Login
        </button>
      </div>
    </div>
  );
}
return (
  <div className="auth-container">
    <div className="form-section">
      <div className="form-card">
        <div className="form-header">
          <AudioWaveform size={48} color="#6366f1" style={{ marginBottom: '1rem' }} />
          <h2 className="form-title">
            {view === 'login' ? 'Welcome to ParseOps' : 'Get Started'}
          </h2>
          <p className="form-subtitle">Where imagination meets innovation</p>
        </div>
        {error && <div className="error-message">{error}</div>}
        {message && <div className="success-message">{message}</div>}
        <form onSubmit={handleAuthAction}>
          <div className="input-group">
            <label className="input-label">Email Address</label>
            <input
              className="input-field"
              type="email"
              placeholder="you@company.com"
              value={formData.email}
              onChange={e => setFormData({ ...formData, email: e.target.value })}
              required
            />
          </div>
          {(view === 'login' || view === 'register') && (
            <div className="input-group">
              <label className="input-label">Password</label>
              <div className="password-wrapper">
                <input
                  className="input-field"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={e => setFormData({ ...formData, password: e.target.value })}
                  required
                />
                <button type="button" className="eye-btn" onClick={() => setShowPassword(!showPassword)}>
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>
          )}
          {view === 'login' && (
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1.5rem' }}>
              <a
                href="#"
                onClick={(e) => { e.preventDefault(); setView('forgot'); setError(''); setMessage(''); }}
                style={{ fontSize: '0.875rem', color: '#6366f1', textDecoration: 'none', fontWeight: 500 }}
              >
                Forgot password?
              </a>
            </div>
          )}
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? <Loader2 className="animate-spin" /> : view === 'login' ? 'Login' : 'Sign Up'}
          </button>
        </form>
        <p className="signup-link">
          {view === 'login' ? (
            <>New to ParseOps? <a href="#" onClick={() => setView('register')}>Start creating for free</a></>
          ) : view === 'register' ? (
            <>Already have an account? <a href="#" onClick={() => setView('login')}>Log in</a></>
          ) : (
            <a href="#" onClick={() => setView('login')}>Back to login</a>
          )}
        </p>
        <div className="divider" style={{ margin: '2rem 0', display: 'flex', alignItems: 'center', gap: '1rem', color: '#94a3b8', fontSize: '0.75rem' }}>
          <div style={{ flex: 1, height: 1, background: '#e2e8f0' }}></div> OR <div style={{ flex: 1, height: 1, background: '#e2e8f0' }}></div>
        </div>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => { window.location.href = `${baseURL}/api/users/auth/microsoft/login/`; }}
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', width: '100%', padding: '0.75rem 0.5rem', fontSize: '0.85rem', fontWeight: 600, whiteSpace: 'nowrap' }}
        >
          <svg style={{ width: 16, height: 16, flexShrink: 0 }} viewBox="0 0 23 23" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="0" y="0" width="10.5" height="10.5" fill="#f25022" />
            <rect x="11.5" y="0" width="10.5" height="10.5" fill="#7fba00" />
            <rect x="0" y="11.5" width="10.5" height="10.5" fill="#00a4ef" />
            <rect x="11.5" y="11.5" width="10.5" height="10.5" fill="#ffb900" />
          </svg>
          Login with Microsoft
        </button>
      </div>
      {/* Fallback In-App Custom Toast for Web Push (Top Center style) */}
      {pushToast && (
        <div style={{
          position: 'fixed',
          top: '20px',
          left: '50%',
          transform: 'translateX(-50%)',
          backgroundColor: '#fff',
          padding: '16px 24px',
          borderRadius: '12px',
          boxShadow: '0 10px 30px rgba(0,0,0,0.15)',
          zIndex: 99999,
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
          borderLeft: '4px solid #6366f1',
          minWidth: '300px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <strong style={{ color: '#0f172a', fontSize: '15px' }}>{pushToast.title}</strong>
            <button onClick={() => setPushToast(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '18px', color: '#94a3b8' }}>×</button>
          </div>
          <span style={{ color: '#475569', fontSize: '14px', lineHeight: '1.4' }}>{pushToast.body}</span>
        </div>
      )}
    </div>
  </div>
);
}
export default App;
