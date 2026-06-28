import re
import os

app_jsx_path = r'c:\Users\saura\ParseOps\frontend\src\App.jsx'

with open(app_jsx_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Use regex to match the exact broken boundary robustly, ignoring whitespace differences
broken_pattern = r'const updateLiveTime = \(\) => \{\s*const \[pendingExtensionCount'

restored_block = """const updateLiveTime = () => {
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

new_content, count = re.subn(broken_pattern, restored_block, content, count=1)

if count > 0:
    with open(app_jsx_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully patched the syntax error in App.jsx!")
else:
    print("Could not find the broken pattern. The file may already be fixed or changed.")
