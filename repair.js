const fs = require('fs');

const appPath = 'frontend/src/App.jsx';
let content = fs.readFileSync(appPath, 'utf8');

// Normalize line endings for reliable matching
content = content.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

const startStr = "    sharing_option: 'specific',";
const endStr = "  const [isFreeMembersModalOpen, setIsFreeMembersModalOpen] = useState(false);";

const startIdx = content.indexOf(startStr);
const endIdx = content.indexOf(endStr, startIdx);

if (startIdx !== -1 && endIdx !== -1) {
    const perfectBlock = `    sharing_option: 'specific',
    shared_viewers: [],
    goal: '',
    impact: 5,
    risk: 'medium'
  });

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
  }, [newTaskData.assignees, newTaskData.estimated_hours, selectedOrg, showCreateModal, view, schedulePreview.manualOverride]);

  const [createAssignMode, setCreateAssignMode] = useState('manual');
  const [createSmartSuggestions, setCreateSmartSuggestions] = useState([]);
  const [createSmartSuggestLoading, setCreateSmartSuggestLoading] = useState(false);
  const [createSmartSuggestError, setCreateSmartSuggestError] = useState(null);

  const [editAssignMode, setEditAssignMode] = useState('manual');
  const [editSmartSuggestions, setEditSmartSuggestions] = useState([]);
  const [editSmartSuggestLoading, setEditSmartSuggestLoading] = useState(false);
  const [editSmartSuggestError, setEditSmartSuggestError] = useState(null);

`;

    content = content.slice(0, startIdx) + perfectBlock + content.slice(endIdx);
    
    // Also remove the lingering schedulePreview block if it exists somewhere else
    const rogueStartStr = '  const [schedulePreview, setSchedulePreview] = useState({';
    let rogueIdx = content.indexOf(rogueStartStr);
    
    // Make sure we don't delete the one we just inserted!
    // The one we just inserted is right after `sharing_option`.
    // So we search starting from AFTER the newly inserted block.
    const insertedEndIdx = startIdx + perfectBlock.length;
    rogueIdx = content.indexOf(rogueStartStr, insertedEndIdx);
    
    if (rogueIdx !== -1) {
        const rogueEndStr = 'schedulePreview.manualOverride]);\n';
        const rogueEndIdx = content.indexOf(rogueEndStr, rogueIdx);
        if (rogueEndIdx !== -1) {
            content = content.slice(0, rogueIdx) + content.slice(rogueEndIdx + rogueEndStr.length);
        }
    }
    
    // Search before the block just in case
    let rogueBeforeIdx = content.slice(0, startIdx).indexOf(rogueStartStr);
    if (rogueBeforeIdx !== -1) {
        const rogueEndStr = 'schedulePreview.manualOverride]);\n';
        const rogueEndIdx = content.indexOf(rogueEndStr, rogueBeforeIdx);
        if (rogueEndIdx !== -1) {
             content = content.slice(0, rogueBeforeIdx) + content.slice(rogueEndIdx + rogueEndStr.length);
        }
    }

    fs.writeFileSync(appPath, content, 'utf8');
    console.log("✅ App.jsx has been completely repaired! Vite should now be fully working.");
} else {
    console.log("Could not find anchor points in App.jsx");
}
