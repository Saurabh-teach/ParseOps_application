import React, { useState, useEffect, useRef } from 'react';
import { Bell, CheckCircle, Trash2, X } from 'lucide-react';
import api, { baseURL } from '../api';

export default function NotificationDropdown({ userId }) {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const dropdownRef = useRef(null);
  const wsRef = useRef(null);

  useEffect(() => {
    fetchNotifications();

    const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const host = baseURL.replace(/^https?:\/\//, '');
    const wsUrl = `${wsScheme}://${host}/ws/notifications/`;
    
    // We only connect if we have a token
    const token = sessionStorage.getItem('access_token');
    if (!token) return;

    wsRef.current = new WebSocket(`${wsUrl}?token=${token}`);
    
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'new_notification') {
        setNotifications((prev) => [data.notification, ...prev]);
        setUnreadCount((prev) => prev + 1);
      }
    };

    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchNotifications = async () => {
    try {
      const res = await api.get('/notifications/');
      setNotifications(res.data);
      setUnreadCount(res.data.filter(n => !n.is_read).length);
    } catch (err) {
      console.error('Failed to fetch notifications:', err);
    }
  };

  const markAsRead = async (id, isRead) => {
    if (isRead) return;
    try {
      await api.post(`/notifications/${id}/mark-read/`);
      setNotifications(notifications.map(n => n.id === id ? { ...n, is_read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err) {
      console.error(err);
    }
  };

  const handleNotificationClick = async (n) => {
    if (!n.is_read) {
      await markAsRead(n.id, false);
    }
    setIsOpen(false);
    if (n.data && n.data.link) {
      window.dispatchEvent(new CustomEvent('navigate_to_task', { detail: { link: n.data.link } }));
    }
  };

  const markAllAsRead = async () => {
    try {
      await api.post('/notifications/mark-all-read/');
      setNotifications(notifications.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error(err);
    }
  };

  const clearAll = async () => {
    try {
      await api.delete('/notifications/clear-all/');
      setNotifications([]);
      setUnreadCount(0);
      setIsOpen(false);
    } catch (err) {
      console.error(err);
    }
  };

  const getIconForType = (type) => {
    switch (type) {
      case 'task_assigned':
      case 'task_queued':
      case 'task_scheduled_from_queue':
        return '📋';
      case 'task_status_changed':
      case 'task_completed':
        return '✅';
      case 'task_rescheduled':
      case 'task_delayed':
      case 'task_overdue':
        return '🕒';
      case 'extension_requested':
      case 'extension_approved':
      case 'extension_rejected':
        return '⏳';
      case 'join_request':
      case 'invitation':
        return '👋';
      default:
        return '🔔';
    }
  };

  return (
    <div className="notification-dropdown" ref={dropdownRef} style={{ position: 'relative' }}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        style={{ 
          background: 'none', border: 'none', cursor: 'pointer', 
          position: 'relative', padding: '0.5rem', display: 'flex', alignItems: 'center' 
        }}
      >
        <Bell size={20} color="#4b5563" />
        {unreadCount > 0 && (
          <span style={{
            position: 'absolute', top: '2px', right: '2px',
            background: '#ef4444', color: 'white', fontSize: '0.65rem',
            padding: '2px 5px', borderRadius: '10px', fontWeight: 'bold'
          }}>
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div style={{
          position: 'absolute', top: '100%', right: '0',
          width: '350px', background: 'white', border: '1px solid #e5e7eb',
          borderRadius: '8px', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
          zIndex: 1000, overflow: 'hidden', display: 'flex', flexDirection: 'column',
          maxHeight: '400px'
        }}>
          <div style={{
            padding: '0.75rem 1rem', borderBottom: '1px solid #e5e7eb',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            background: '#f9fafb'
          }}>
            <h3 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600, color: '#111827' }}>Notifications</h3>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {unreadCount > 0 && (
                <button 
                  onClick={markAllAsRead}
                  style={{ background: 'none', border: 'none', fontSize: '0.75rem', color: '#6366f1', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.2rem' }}
                >
                  <CheckCircle size={14} /> Mark all read
                </button>
              )}
              {notifications.length > 0 && (
                <button 
                  onClick={clearAll}
                  style={{ background: 'none', border: 'none', fontSize: '0.75rem', color: '#ef4444', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.2rem' }}
                >
                  <Trash2 size={14} /> Clear all
                </button>
              )}
            </div>
          </div>

          <div style={{ overflowY: 'auto', flex: 1 }}>
            {notifications.length === 0 ? (
              <div style={{ padding: '2rem 1rem', textAlign: 'center', color: '#6b7280', fontSize: '0.85rem' }}>
                You have no notifications.
              </div>
            ) : (
              notifications.map((n) => (
                <div 
                  key={n.id} 
                  onClick={() => handleNotificationClick(n)}
                  style={{
                    padding: '0.75rem 1rem', borderBottom: '1px solid #f3f4f6',
                    background: n.is_read ? 'white' : '#eff6ff',
                    cursor: 'pointer', display: 'flex', gap: '0.75rem',
                    transition: 'background 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = '#f9fafb'}
                  onMouseLeave={(e) => e.currentTarget.style.background = n.is_read ? 'white' : '#eff6ff'}
                >
                  <div style={{ fontSize: '1.2rem', paddingTop: '2px' }}>
                    {getIconForType(n.notification_type)}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '0.85rem', fontWeight: n.is_read ? 500 : 600, color: '#111827', marginBottom: '2px' }}>
                      {n.title}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#4b5563', lineHeight: 1.4 }}>
                      {n.message}
                    </div>
                    <div style={{ fontSize: '0.65rem', color: '#9ca3af', marginTop: '4px' }}>
                      {new Date(n.created_at).toLocaleString()}
                    </div>
                  </div>
                  {!n.is_read && (
                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#3b82f6', marginTop: '6px' }} />
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
