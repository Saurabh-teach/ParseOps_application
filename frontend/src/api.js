import axios from 'axios';

export const baseURL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const API_BASE_URL = `${baseURL}/api`;

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 8000, // 8-second timeout to prevent indefinite hangs
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to automatically add authorization token
api.interceptors.request.use(
  (config) => {
    const token = sessionStorage.getItem('access_token');
    if (token) {
      if (config.headers && typeof config.headers.set === 'function') {
        config.headers.set('Authorization', `Bearer ${token}`);
      } else {
        config.headers['Authorization'] = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Helper to set/remove auth tokens
export const setAuthTokens = (access, refresh) => {
  if (access) {
    api.defaults.headers.common['Authorization'] = `Bearer ${access}`;
    sessionStorage.setItem('access_token', access);
    if (refresh) sessionStorage.setItem('refresh_token', refresh);
  } else {
    delete api.defaults.headers.common['Authorization'];
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('refresh_token');
  }
};

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refresh = sessionStorage.getItem('refresh_token');
      
      if (refresh) {
        try {
          const response = await axios.post(`${API_BASE_URL}/token/refresh/`, { refresh }, { timeout: 8000 });
          const { access, refresh: newRefresh } = response.data;
          setAuthTokens(access, newRefresh || refresh);
          originalRequest.headers['Authorization'] = `Bearer ${access}`;
          return api(originalRequest);
        } catch (err) {
          setAuthTokens(null);
          // Only redirect if not already on /login to prevent infinite loop
          if (!window.location.pathname.startsWith('/login')) {
            window.location.href = '/login';
          }
          return Promise.reject(err);
        }
      } else {
        setAuthTokens(null);
        // Only redirect if not already on /login to prevent infinite loop
        if (!window.location.pathname.startsWith('/login')) {
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    }
    
    // Check if the user lost access to the organization (e.g. removed by owner)
    const errDetail = error.response?.data?.detail || error.response?.data?.error || "";
    const isRemovalError = 
      errDetail === "You are not an active member of this organization." ||
      errDetail === "You are not a member of this organization." ||
      errDetail === "User is not a member of this organization.";
      
    if (error.response?.status === 403 || error.response?.status === 404) {
      if (
        isRemovalError || 
        (error.response?.status === 404 && originalRequest.url && originalRequest.url.includes('/api/organizations/'))
      ) {
        window.dispatchEvent(new Event('workspace_access_lost'));
      }
    }
    
    return Promise.reject(error);
  }
);

// Login Flow
export const loginRequest = async (email, password) => {
  const response = await api.post('/users/login/', { email, password });
  return response.data;
};

export const verifyLoginOTP = async (email, otp) => {
  const response = await api.post('/users/verify-login-otp/', { email, otp });
  return response.data;
};

export const getSAMLConfigurations = async () => {
  const response = await api.get('/organizations/saml/configs/');
  return response.data;
};


// Registration Flow
export const registerRequest = async (userData) => {
  const response = await api.post('/users/register/', userData);
  return response.data;
};

export const verifyRegistrationOTP = async (email, otp) => {
  const response = await api.post('/users/verify-registration-otp/', { email, otp });
  return response.data;
};

// Resend Helpers
export const resendLoginOTP = async (email) => {
  const response = await api.post('/users/resend-login-otp/', { email });
  return response.data;
};

export const resendRegistrationOTP = async (email) => {
  const response = await api.post('/users/resend-registration-otp/', { email });
  return response.data;
};

export const logout = async () => {
  const refresh = sessionStorage.getItem('refresh_token');
  await api.post('/users/logout/', { refresh });
  setAuthTokens(null);
};

export const forgotPasswordRequest = async (email) => {
  const response = await api.post('/users/forgot-password/', { email });
  return response.data;
};

export const resetPasswordVerify = async (email, otp, password) => {
  const response = await api.post('/users/reset-password-verify/', { email, otp, password });
  return response.data;
};

export const changePassword = async (email, new_password) => {
  const response = await api.post('/users/change-password/', { email, new_password });
  return response.data;
};

// User Profile Endpoints
export const getUserProfile = async () => {
  const response = await api.get('/users/profile/');
  return response.data;
};

export const updateUserProfile = async (formData) => {
  const headers = formData instanceof FormData ? { 'Content-Type': 'multipart/form-data' } : {};
  const response = await api.patch('/users/profile/', formData, { headers });
  return response.data;
};

export const requestEmailChange = async (newEmail, password) => {
  const response = await api.post('/users/request-email-change/', { new_email: newEmail, password });
  return response.data;
};

export const verifyEmailChange = async (newEmail, otp) => {
  const response = await api.post('/users/verify-email-change/', { new_email: newEmail, otp });
  return response.data;
};

export const applyLeave = async (data) => {
  const headers = data instanceof FormData ? { 'Content-Type': 'multipart/form-data' } : {};
  const response = await api.post('/users/leaves/', data, { headers });
  return response.data;
};

export const getUserLeaves = async (orgId) => {
  const response = await api.get(`/users/leaves/?organization=${orgId}`);
  return response.data;
};

export const getAllLeaves = async (orgId) => {
  const response = await api.get(`/users/leaves/all/?organization=${orgId}`);
  return response.data;
};

export const approveLeave = async (leaveId) => {
  const response = await api.post(`/users/leaves/${leaveId}/approve/`);
  return response.data;
};

export const rejectLeave = async (leaveId, reason = '') => {
  const response = await api.post(`/users/leaves/${leaveId}/reject/`, { reason });
  return response.data;
};

export const cancelLeave = async (leaveId, reason = '') => {
  const response = await api.post(`/users/leaves/${leaveId}/cancel/`, { reason });
  return response.data;
};

export const getLeaveBalances = async (orgId) => {
  const response = await api.get(`/users/leave-balances/?organization=${orgId}`);
  return response.data;
};

// Organization APIs
export const getOrganizations = async () => {
  const response = await api.get('/organizations/');
  return response.data;
};

export const getMyWorkspaces = async () => {
  const response = await api.get('/organizations/my-workspaces/');
  return response.data;
};

export const createOrganization = async (data) => {
  const response = await api.post('/organizations/', data);
  return response.data;
};

export const sendJoinRequest = async (orgId, role, message = '') => {
  const response = await api.post(`/organizations/${orgId}/join-request/`, { requested_role: role, message });
  return response.data;
};

export const inviteMember = async (orgId, email, role, message = '') => {
  const response = await api.post(`/organizations/${orgId}/invite/`, { email, role, message });
  return response.data;
};

export const getPendingInvitations = async (orgId) => {
  const response = await api.get(`/organizations/${orgId}/pending-invitations/`);
  return response.data;
};

export const cancelInvitation = async (orgId, invitationId) => {
  const response = await api.post(`/organizations/${orgId}/cancel-invitation/`, { invitation_id: invitationId });
  return response.data;
};

export const getOrganizationMembers = async (orgId) => {
  const response = await api.get(`/organizations/${orgId}/members/`);
  return response.data;
};

export const getJoinRequests = async (orgId) => {
  const response = await api.get(`/organizations/${orgId}/join-requests/`);
  return response.data;
};

export const manageJoinRequest = async (orgId, requestId, action) => {
  const response = await api.post(`/organizations/${orgId}/manage-request/`, { request_id: requestId, action });
  return response.data;
};

export const acceptInvitation = async (invitationId, token = null) => {
  const response = await api.post('/organizations/accept-invitation/', { invitation_id: invitationId, token });
  return response.data;
};

export const declineInvitation = async (invitationId, token = null) => {
  const response = await api.post('/organizations/decline-invitation/', { invitation_id: invitationId, token });
  return response.data;
};

export const getNotifications = async (orgSlug = null, memberId = null) => {
  let url = '/notifications/';
  if (orgSlug) {
      url += `?org=${orgSlug}`;
      if (memberId) url += `&member=${memberId}`;
  }
  const response = await api.get(url);
  return response.data;
};

export const markAllNotificationsRead = async (orgSlug = null) => {
  let url = '/notifications/mark-all-read/';
  if (orgSlug) {
    url += `?org=${orgSlug}`;
  }
  const response = await api.post(url);
  return response.data;
};

export const markNotificationRead = async (id) => {
  const response = await api.post(`/notifications/${id}/mark-read/`);
  return response.data;
};

export const updateOrganization = async (orgId, data) => {
  const headers = data instanceof FormData ? { 'Content-Type': 'multipart/form-data' } : {};
  const response = await api.patch(`/organizations/${orgId}/`, data, { headers });
  return response.data;
};

export const deleteOrganization = async (orgId) => {
  const response = await api.delete(`/organizations/${orgId}/`);
  return response.data;
};

export const deactivateOrganization = async (orgId) => {
  const response = await api.post(`/organizations/${orgId}/deactivate/`);
  return response.data;
};

export const reactivateOrganization = async (orgId) => {
  const response = await api.post(`/organizations/${orgId}/reactivate/`);
  return response.data;
};

export const removeMember = async (orgId, memberId) => {
  const response = await api.post(`/organizations/${orgId}/remove-member/`, { member_id: memberId });
  return response.data;
};

export const changeMemberRole = async (orgId, memberId, role) => {
  const response = await api.post(`/organizations/${orgId}/change-role/`, { member_id: memberId, role });
  return response.data;
};

export const getWorkspaceHistory = async (orgId, memberId = null) => {
  let url = `/organizations/${orgId}/history/`;
  if (memberId) url += `?member=${memberId}`;
  const response = await api.get(url);
  return response.data;
};

// Notes API Endpoints
export const getNotes = async (orgId) => {
  const url = orgId ? `/notes/?organization=${orgId}` : '/notes/';
  const response = await api.get(url);
  return response.data;
};

export const createNote = async (data) => {
  const response = await api.post('/notes/', data);
  return response.data;
};

export const updateNote = async (noteId, data) => {
  const response = await api.patch(`/notes/${noteId}/`, data);
  return response.data;
};

export const deleteNote = async (noteId) => {
  const response = await api.delete(`/notes/${noteId}/`);
  return response.data;
};

export const restoreMember = async (orgId, memberId) => {
  const response = await api.post(`/organizations/${orgId}/restore-member/`, { member_id: memberId });
  return response.data;
};

export const restoreNote = async (noteId) => {
  const response = await api.post(`/notes/${noteId}/restore/`);
  return response.data;
};

// Goals API Endpoints
export const getGoals = async (orgId) => {
  const url = orgId ? `/goals/?organization=${orgId}` : '/goals/';
  const response = await api.get(url);
  return response.data;
};

export const createGoal = async (orgId, data) => {
  const response = await api.post(`/goals/?organization=${orgId}`, data);
  return response.data;
};

export const getGoalDetail = async (goalId) => {
  const response = await api.get(`/goals/${goalId}/`);
  return response.data;
};

export const updateGoal = async (goalId, data) => {
  const response = await api.patch(`/goals/${goalId}/`, data);
  return response.data;
};

export const deleteGoal = async (goalId) => {
  const response = await api.delete(`/goals/${goalId}/`);
  return response.data;
};

export const restoreGoal = async (goalId) => {
  const response = await api.post(`/goals/${goalId}/restore/`);
  return response.data;
};

// Key Results API Endpoints
export const getKeyResults = async (goalId) => {
  const response = await api.get(`/goals/${goalId}/key-results/`);
  return response.data;
};

export const createKeyResult = async (goalId, data) => {
  const response = await api.post(`/goals/${goalId}/key-results/`, data);
  return response.data;
};

export const updateKeyResult = async (goalId, krId, data) => {
  const response = await api.patch(`/goals/${goalId}/key-results/${krId}/`, data);
  return response.data;
};

export const deleteKeyResult = async (goalId, krId) => {
  const response = await api.delete(`/goals/${goalId}/key-results/${krId}/`);
  return response.data;
};

// Tasks API Endpoints
export const getTasks = async (orgId, params = {}) => {
  const response = await api.get(`/organizations/${orgId}/tasks/filter/`, { params });
  return response.data;
};

export const createTask = async (data) => {
  const response = await api.post(`/tasks/create/`, data);
  return response.data;
};

export const getTaskDetail = async (taskId) => {
  const response = await api.get(`/tasks/${taskId}/`);
  return response.data;
};

export const updateTask = async (taskId, data) => {
  const response = await api.patch(`/tasks/${taskId}/`, data);
  return response.data;
};

export const updateTaskStatus = async (taskId, status) => {
  const response = await api.patch(`/tasks/${taskId}/update-status/`, { status });
  return response.data;
};

export const deleteTask = async (taskId) => {
  const response = await api.delete(`/tasks/${taskId}/soft-delete/`);
  return response.data;
};

// Task Comments APIs
export const getTaskComments = async (taskId) => {
  const response = await api.get(`/tasks/${taskId}/comments/`);
  return response.data;
};

export const createTaskComment = async (taskId, commentText, parentId = null, attachmentIds = []) => {
  const response = await api.post(`/tasks/${taskId}/comments/create/`, {
    comment: commentText,
    parent: parentId,
    attachment_ids: attachmentIds
  });
  return response.data;
};

export const updateTaskComment = async (commentId, commentText) => {
  const response = await api.put(`/comments/${commentId}/`, { comment: commentText });
  return response.data;
};

export const deleteTaskComment = async (commentId) => {
  const response = await api.delete(`/comments/${commentId}/`);
  return response.data;
};

export const replyToComment = async (commentId, commentText, attachmentIds = []) => {
  const response = await api.post(`/comments/${commentId}/reply/`, {
    comment: commentText,
    attachment_ids: attachmentIds
  });
  return response.data;
};

// Slug-based Workspace Goals API Endpoints
export const getOrgGoals = async (orgSlug) => {
  const response = await api.get(`/org/${orgSlug}/goals/`);
  return response.data;
};

export const createOrgGoal = async (orgSlug, data) => {
  const response = await api.post(`/org/${orgSlug}/goals/`, data);
  return response.data;
};

export const getOrgGoalDetail = async (orgSlug, goalId) => {
  const response = await api.get(`/org/${orgSlug}/goals/${goalId}/`);
  return response.data;
};

export const updateOrgGoal = async (orgSlug, goalId, data) => {
  const response = await api.patch(`/org/${orgSlug}/goals/${goalId}/`, data);
  return response.data;
};

export const deleteOrgGoal = async (orgSlug, goalId) => {
  const response = await api.delete(`/org/${orgSlug}/goals/${goalId}/`);
  return response.data;
};

export const applyTemplateToGoal = async (orgSlug, templateId, goalId) => {
  const response = await api.post(`/org/${orgSlug}/templates/${templateId}/apply/`, { goal_id: goalId });
  return response.data;
};

// Slug-based Workspace Tasks API Endpoints
export const getOrgTasks = async (orgSlug) => {
  const response = await api.get(`/org/${orgSlug}/tasks/`);
  return response.data;
};

export const createOrgTask = async (orgSlug, data) => {
  const response = await api.post(`/org/${orgSlug}/tasks/`, data);
  return response.data;
};

export const getOrgTaskDetail = async (orgSlug, taskId) => {
  const response = await api.get(`/org/${orgSlug}/tasks/${taskId}/`);
  return response.data;
};

export const updateOrgTask = async (orgSlug, taskId, data) => {
  const response = await api.patch(`/org/${orgSlug}/tasks/${taskId}/`, data);
  return response.data;
};

export const deleteOrgTask = async (orgSlug, taskId) => {
  const response = await api.delete(`/org/${orgSlug}/tasks/${taskId}/`);
  return response.data;
};

// Web Push Notifications
export const saveWebPushSubscription = async (subscriptionData) => {
  const response = await api.post('/notifications/webpush-subscribe/', subscriptionData);
  return response.data;
};

export const getTasksKanban = async (orgId) => {
  const response = await api.get(`/organizations/${orgId}/tasks/kanban/`);
  return response.data;
};

export const updateTaskTicketStatus = async (ticketId, status, add_time_minutes = undefined) => {
  const payload = {};
  if (status !== undefined) payload.status = status;
  if (add_time_minutes !== undefined) payload.add_time_minutes = add_time_minutes;
  const response = await api.patch(`/tasks/tickets/${ticketId}/update-status/`, payload);
  return response.data;
};

export const getDashboardAnalytics = async (orgId, params = {}) => {
  const response = await api.get(`/analytics/org/${orgId}/`, { params });
  return response.data;
};

// Extension Requests
export const getExtensionRequests = async (orgId) => {
  const response = await api.get(`/organizations/${orgId}/extension-requests/`);
  return response.data;
};

export const reviewExtensionRequest = async (requestId, data) => {
  const response = await api.patch(`/extension-requests/${requestId}/review/`, data);
  return response.data;
};

export const submitTaskProof = async (taskId, formData) => {
  const response = await api.post(`/tasks/${taskId}/submit/`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    }
  });
  return response.data;
};

// Template Library APIs
export const getTemplates = async (orgSlug) => {
  const response = await api.get(`/org/${orgSlug}/templates/`);
  return response.data;
};

export const createTemplate = async (orgSlug, data) => {
  const response = await api.post(`/org/${orgSlug}/templates/`, data);
  return response.data;
};

export const createGoalFromTemplate = async (orgSlug, templateId, data) => {
  const response = await api.post(`/org/${orgSlug}/templates/${templateId}/create_and_apply/`, data);
  return response.data;
};

export const updateTemplate = async (orgSlug, templateId, data) => {
  const response = await api.put(`/org/${orgSlug}/templates/${templateId}/`, data);
  return response.data;
};

export const deleteTemplate = async (orgSlug, templateId) => {
  const response = await api.delete(`/org/${orgSlug}/templates/${templateId}/`);
  return response.data;
};

// CSV Import API
export const importCSV = async (orgSlug, formData) => {
  const response = await api.post(`/org/${orgSlug}/import-csv/`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    }
  });
  return response.data;
};

export const importTemplateFile = async (orgSlug, formData) => {
  const response = await api.post(`/org/${orgSlug}/templates/import-file/`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    }
  });
  return response.data;
};

export const getSmartSuggest = async (orgId, params) => {
  const response = await api.get(`/organizations/${orgId}/tasks/smart-suggest/`, { params });
  return response.data;
};

export const checkFreeMembers = async (orgId) => {
  const response = await api.get(`/organizations/${orgId}/tasks/check-free-members/`);
  return response.data;
};

export const assignSuggestedTask = async (orgId, taskId, userId) => {
  const response = await api.post(`/organizations/${orgId}/tasks/assign-suggested/`, { task_id: taskId, user_id: userId });
  return response.data;
};

export const changeAssigneeOverride = async (taskId, userId) => {
  const response = await api.patch(`/tasks/${taskId}/change-assignee/`, { user_id: userId });
  return response.data;
};

export const manualScheduleTasks = async (orgId, userId = null) => {
  const payload = {};
  if (userId) payload.user_id = userId;
  const response = await api.post(`/organizations/${orgId}/tasks/manual-schedule/`, payload);
  return response.data;
};

export const bulkScheduleTasks = async (orgId) => {
  const response = await api.post(`/organizations/${orgId}/tasks/bulk-schedule/`);
  return response.data;
};

export const previewScheduleTasks = async (orgId, numDays) => {
  const response = await api.get(`/organizations/${orgId}/tasks/preview-schedule/`, { params: { num_days: numDays } });
  return response.data;
};

export const applyScheduleTasks = async (orgId, assignments) => {
  const response = await api.post(`/organizations/${orgId}/tasks/apply-schedule/`, { assignments });
  return response.data;
};

export const schedulePreview = async (orgId, assigneeId, estimatedHours, taskId = null) => {
  const payload = { assignee: assigneeId, estimated_hours: estimatedHours };
  if (taskId) payload.task_id = taskId;
  const response = await api.post(`/organizations/${orgId}/tasks/schedule-preview/`, payload);
  return response.data;
};

export const runScheduler = async (orgSlug) => {
  const response = await api.post(`/organizations/${orgSlug}/tasks/run_scheduler/`);
  return response.data;
};

export const importTasksCSV = async (orgSlug, file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post(`/organizations/${orgSlug}/tasks/import_csv/`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    }
  });
  return response.data;
};

export default api;

