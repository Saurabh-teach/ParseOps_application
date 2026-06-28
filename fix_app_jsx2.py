import os
import sys

app_jsx_path = r'c:\Users\saura\ParseOps\frontend\src\App.jsx'

with open(app_jsx_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Restore the broken useEffect and state
broken_marker = "    const updateLiveTime = () => {\n  const [pendingExtensionCount"
restored_block = """    const updateLiveTime = () => {
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

  const [pendingExtensionCount"""

content = content.replace(broken_marker, restored_block)


# 2. Remove the selected assignee stats block
stats_block = """                              {(() => {
                                const selectedId = newTaskData.assignees && newTaskData.assignees[0];
                                if (!selectedId) return null;
                                const stats = getMemberStats(selectedId);
                                if (!stats) return null;
                                return (
                                  <div style={{ fontSize: '0.78rem', color: '#475569', background: '#f8fafc', padding: '0.4rem 0.6rem', borderRadius: '6px', border: '1px solid #cbd5e1', marginTop: '0.25rem' }}>
                                    📈 <strong>Past Performance:</strong> {stats.performance}% | ⚡ <strong>Efficiency:</strong> {stats.efficiency}x | 💼 Completed {stats.completed} similar tasks
                                  </div>
                                );
                              })()}"""
content = content.replace(stats_block, "")

# 3. Fix the topSugg block
sugg_before = """                                      const topSugg = createSmartSuggestions[0];
                                      const stats = getMemberStats(topSugg.id);
                                      const isAssigned = newTaskData.assignees && newTaskData.assignees[0] === topSugg.id;
                                      const isNewMember = (topSugg.reason || '').includes('New member');"""
sugg_after = """                                      const topSugg = createSmartSuggestions[0];
                                      const isAssigned = newTaskData.assignees && newTaskData.assignees[0] === topSugg.id;
                                      const isNewMember = (topSugg.reason || '').includes('New member');"""
content = content.replace(sugg_before, sugg_after)

# 4. Remove the stats UI in topSugg
stats_sugg_ui = """                                          {stats && (
                                            <div style={{ fontSize: '0.74rem', color: '#64748b' }}>
                                              Past Performance: {isNewMember ? '70% (new member baseline)' : `${stats.performance}%`} | Efficiency: {stats.efficiency}x
                                            </div>
                                          )}"""
content = content.replace(stats_sugg_ui, "")


with open(app_jsx_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("App.jsx has been safely fixed and updated.")
