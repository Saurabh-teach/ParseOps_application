import { useState, useEffect, useCallback } from 'react';
import { 
  Folder, FileText, CheckSquare, ListTodo, Paperclip, Link as LinkIcon, 
  Plus, Trash2, Edit2, ChevronRight, ChevronDown, Save, Target,
  Upload, FileSpreadsheet, AlertCircle
} from 'lucide-react';
import { getTemplates, createTemplate, createGoalFromTemplate, importTemplateFile, updateTemplate, deleteTemplate } from '../../api';

const FolderItem = ({ folder, updateFolder, deleteFolder }) => {
  const [expanded, setExpanded] = useState(true);
  
  const addItem = (type) => {
    updateFolder({
      ...folder,
      items: [...(folder.items || []), { 
        id: Math.random().toString(), 
        name: `New ${type}`, 
        item_type: type 
      }]
    });
  };

  const addSubfolder = () => {
    updateFolder({
      ...folder,
      subfolders: [...(folder.subfolders || []), { 
        id: Math.random().toString(), 
        name: 'New Subfolder', 
        items: [], 
        subfolders: [] 
      }]
    });
  };

  const updateSubfolder = (subId, updatedSub) => {
    updateFolder({
      ...folder,
      subfolders: folder.subfolders.map(sub => sub.id === subId ? updatedSub : sub)
    });
  };

  const deleteSubfolder = (subId) => {
    updateFolder({
      ...folder,
      subfolders: folder.subfolders.filter(sub => sub.id !== subId)
    });
  };

  const updateItemName = (itemId, newName) => {
    updateFolder({
      ...folder,
      items: folder.items.map(item => item.id === itemId ? { ...item, name: newName } : item)
    });
  };

  const deleteItem = (itemId) => {
    updateFolder({
      ...folder,
      items: folder.items.filter(item => item.id !== itemId)
    });
  };

  const getItemIcon = (type) => {
    switch(type) {
      case 'document': return <FileText size={14} />;
      case 'checklist': return <CheckSquare size={14} />;
      case 'task_list': return <ListTodo size={14} />;
      case 'file': return <Paperclip size={14} />;
      case 'link': return <LinkIcon size={14} />;
      case 'task': return <CheckSquare size={14} style={{ color: '#10b981' }} />;
      default: return <FileText size={14} />;
    }
  };

  return (
    <div style={{ marginLeft: '1.5rem', marginBottom: '0.5rem', borderLeft: '1px solid #e2e8f0', paddingLeft: '1rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
        <button onClick={() => setExpanded(!expanded)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
          {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        </button>
        <Folder size={16} style={{ color: '#6366f1' }} />
        <input 
          value={folder.name}
          onChange={(e) => updateFolder({...folder, name: e.target.value})}
          style={{ border: 'none', background: 'transparent', fontWeight: 600, fontSize: '0.95rem', outline: 'none' }}
        />
        <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.5rem' }}>
          <button onClick={() => addItem('document')} style={{ background: '#f1f5f9', border: 'none', borderRadius: '4px', padding: '0.2rem 0.5rem', fontSize: '0.75rem', cursor: 'pointer' }}>+ Doc</button>
          <button onClick={() => addItem('task')} style={{ background: '#f1f5f9', border: 'none', borderRadius: '4px', padding: '0.2rem 0.5rem', fontSize: '0.75rem', cursor: 'pointer', color: '#10b981', fontWeight: 600 }}>+ Task</button>
          <button onClick={() => addItem('task_list')} style={{ background: '#f1f5f9', border: 'none', borderRadius: '4px', padding: '0.2rem 0.5rem', fontSize: '0.75rem', cursor: 'pointer' }}>+ Tasks</button>
          <button onClick={addSubfolder} style={{ background: '#f1f5f9', border: 'none', borderRadius: '4px', padding: '0.2rem 0.5rem', fontSize: '0.75rem', cursor: 'pointer' }}>+ Folder</button>
          <button onClick={deleteFolder} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer' }}><Trash2 size={14} /></button>
        </div>
      </div>

      {expanded && (
        <div style={{ paddingLeft: '1.5rem' }}>
          {/* Render Items */}
          {(folder.items || []).map(item => (
            <div key={item.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.25rem 0', color: '#475569' }}>
              {getItemIcon(item.item_type)}
              <input 
                value={item.name}
                onChange={(e) => updateItemName(item.id, e.target.value)}
                style={{ border: 'none', background: 'transparent', fontSize: '0.85rem', outline: 'none', flex: 1 }}
              />
              <button 
                onClick={() => window.dispatchEvent(new CustomEvent('open-template-item-editor', { detail: { item, folderId: folder.id } }))}
                style={{ background: '#f1f5f9', border: 'none', borderRadius: '4px', padding: '0.2rem 0.5rem', fontSize: '0.75rem', cursor: 'pointer', color: '#6366f1', fontWeight: 600 }}
              >
                Edit Content
              </button>
              <button onClick={() => deleteItem(item.id)} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}><Trash2 size={14} /></button>
            </div>
          ))}

          {/* Render Subfolders */}
          {(folder.subfolders || []).map(sub => (
            <FolderItem 
              key={sub.id} 
              folder={sub} 
              updateFolder={(updated) => updateSubfolder(sub.id, updated)}
              deleteFolder={() => deleteSubfolder(sub.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const findPlaceholders = (template) => {
  const placeholders = new Set();
  const regex = /\{([A-Za-z0-9_ -]+)\}/g;

  const scanText = (text) => {
    if (!text || typeof text !== 'string') return;
    let match;
    regex.lastIndex = 0;
    while ((match = regex.exec(text)) !== null) {
      placeholders.add(match[1]);
    }
  };

  const scanContent = (content) => {
    if (!content) return;
    if (typeof content === 'string') {
      scanText(content);
    } else if (Array.isArray(content)) {
      content.forEach(val => scanContent(val));
    } else if (typeof content === 'object') {
      Object.values(content).forEach(val => scanContent(val));
    }
  };

  const scanFolder = (folder) => {
    scanText(folder.name);
    scanText(folder.description);
    
    if (folder.items) {
      folder.items.forEach(item => {
        scanText(item.name);
        scanText(item.url);
        scanContent(item.content);
      });
    }
    
    if (folder.subfolders) {
      folder.subfolders.forEach(sub => scanFolder(sub));
    }
  };

  if (template.folders) {
    template.folders.forEach(folder => scanFolder(folder));
  }

  return Array.from(placeholders);
};

const replacePlaceholders = (text, values) => {
  if (!text || typeof text !== 'string') return text;
  let result = text;
  Object.keys(values).forEach(key => {
    const val = values[key] !== '' ? values[key] : `{${key}}`;
    result = result.replaceAll(`{${key}}`, val);
  });
  return result;
};

const PreviewFolder = ({ folder, placeholderValues }) => {
  const [expanded, setExpanded] = useState(true);
  const folderName = replacePlaceholders(folder.name, placeholderValues);
  
  return (
    <div style={{ marginLeft: '0.75rem', marginTop: '0.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 600, color: '#334155', fontSize: '0.9rem' }}>
        <button onClick={() => setExpanded(!expanded)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'flex', alignItems: 'center', color: '#64748b' }}>
          {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </button>
        <Folder size={14} style={{ color: '#6366f1' }} />
        <span>{folderName}</span>
      </div>
      
      {expanded && (
        <div style={{ paddingLeft: '1.25rem', borderLeft: '1px dashed #cbd5e1', marginLeft: '0.4rem' }}>
          {/* Render Items */}
          {folder.items && folder.items.map(item => {
            const itemName = replacePlaceholders(item.name, placeholderValues);
            const itemType = item.item_type;
            
            let icon = <FileText size={12} style={{ color: '#64748b' }} />;
            if (itemType === 'task') {
              icon = <CheckSquare size={12} style={{ color: '#10b981' }} />;
            } else if (itemType === 'checklist') {
              icon = <ListTodo size={12} style={{ color: '#f59e0b' }} />;
            } else if (itemType === 'link') {
              icon = <LinkIcon size={12} style={{ color: '#3b82f6' }} />;
            } else if (itemType === 'file') {
              icon = <Paperclip size={12} style={{ color: '#6b7280' }} />;
            }
            
            return (
              <div key={item.id} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.82rem', color: '#475569', padding: '0.2rem 0' }}>
                {icon}
                <span>{itemName}</span>
                {itemType === 'task' && (
                  <span style={{ fontSize: '0.7rem', color: '#94a3b8', marginLeft: '0.25rem' }}>
                    ({item.content?.priority || 'medium'}{item.content?.estimated_hours ? `, ${item.content.estimated_hours}h` : ''})
                  </span>
                )}
              </div>
            );
          })}
          
          {/* Render Subfolders */}
          {folder.subfolders && folder.subfolders.map(sub => (
            <PreviewFolder key={sub.id} folder={sub} placeholderValues={placeholderValues} />
          ))}
        </div>
      )}
    </div>
  );
};

const TemplateManager = ({ orgSlug, onApplyTemplate }) => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const fetchTemplates = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getTemplates(orgSlug);
      setTemplates(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [orgSlug]);

  // Builder state
  const [showBuilder, setShowBuilder] = useState(false);
  const [activeEditor, setActiveEditor] = useState(null); // { item, folderId }
  const [builderData, setBuilderData] = useState({
    name: 'New Template',
    description: '',
    visibility: 'public',
    folders: []
  });

  const [editingTemplateId, setEditingTemplateId] = useState(null);

  const handleEditTemplate = (template) => {
    setEditingTemplateId(template.id);
    setBuilderData({
      name: template.name || '',
      description: template.description || '',
      visibility: template.visibility || 'public',
      folders: template.folders || []
    });
    setShowBuilder(true);
  };

  const handleDeleteTemplate = async (templateId, templateName) => {
    if (!window.confirm(`Are you sure you want to delete the template "${templateName}"?`)) {
      return;
    }
    try {
      setLoading(true);
      await deleteTemplate(orgSlug, templateId);
      alert('Template deleted successfully!');
      fetchTemplates();
    } catch (err) {
      console.error(err);
      alert(`Error deleting template: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelBuilder = () => {
    setShowBuilder(false);
    setEditingTemplateId(null);
    setBuilderData({
      name: 'New Template',
      description: '',
      visibility: 'public',
      folders: []
    });
  };

  // CSV/Excel Import state
  const [showImportModal, setShowImportModal] = useState(false);
  const [importFile, setImportFile] = useState(null);
  const [importProgress, setImportProgress] = useState(null);
  const [importError, setImportError] = useState(null);
  const [parsedData, setParsedData] = useState(null);
  const [editedGoalTitle, setEditedGoalTitle] = useState('');
  const [editedTemplateDescription, setEditedTemplateDescription] = useState('');

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImportFile(file);
      setImportError(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      const ext = file.name.split('.').pop().toLowerCase();
      if (ext === 'csv' || ext === 'xlsx' || ext === 'xls') {
        setImportFile(file);
        setImportError(null);
      } else {
        setImportError('Unsupported file type. Please drop a CSV or Excel file.');
      }
    }
  };

  const handleUpload = async () => {
    if (!importFile) return;

    const formData = new FormData();
    formData.append('file', importFile);

    setImportProgress(10);
    setImportError(null);

    // Smooth progress simulation
    const interval = setInterval(() => {
      setImportProgress(prev => {
        if (prev === null) return null;
        if (prev >= 90) {
          clearInterval(interval);
          return 90;
        }
        return prev + 15;
      });
    }, 150);

    try {
      const response = await importTemplateFile(orgSlug, formData);
      clearInterval(interval);
      setImportProgress(100);
      
      setTimeout(() => {
        setParsedData(response);
        const fileNameWithoutExt = importFile.name ? importFile.name.replace(/\.[^/.]+$/, "") : "";
        setEditedGoalTitle(fileNameWithoutExt || response.goal_title || 'Imported Template');
        setEditedTemplateDescription('');
        setImportProgress(null);
      }, 300);

    } catch (err) {
      clearInterval(interval);
      setImportProgress(null);
      const msg = err.response?.data?.error || err.message || 'Error processing file.';
      setImportError(msg);
      console.error(err);
    }
  };

  const handleLoadIntoBuilder = () => {
    if (!parsedData) return;
    setBuilderData({
      name: editedGoalTitle || 'Imported Template',
      description: editedTemplateDescription || '',
      visibility: 'public',
      folders: parsedData.folder_data || []
    });
    setShowBuilder(true);
    setShowImportModal(false);
    // Reset import states
    setImportFile(null);
    setParsedData(null);
    setImportError(null);
  };

  // Wizard state
  const [activeTemplateForWizard, setActiveTemplateForWizard] = useState(null);
  const [wizardGoalData, setWizardGoalData] = useState({
    title: '',
    description: '',
    due_date: '',
    priority: 'medium',
    timeframe: 'quarterly',
  });
  const [wizardPlaceholders, setWizardPlaceholders] = useState({});
  const [wizardVariables, setWizardVariables] = useState([]);

  const openTemplateWizard = (template) => {
    setActiveTemplateForWizard(template);
    setWizardGoalData({
      title: template.name || '',
      description: template.description || '',
      due_date: '',
      priority: 'medium',
      timeframe: 'quarterly',
    });

    const vars = findPlaceholders(template);
    setWizardVariables(vars);

    const initialValues = {};
    vars.forEach(v => {
      initialValues[v] = '';
    });
    setWizardPlaceholders(initialValues);
  };

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        setLoading(true);
        const templateData = await getTemplates(orgSlug);
        if (cancelled) return;
        setTemplates(templateData);
      } catch (err) {
        console.error(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => { cancelled = true; };
  }, [orgSlug]);

  useEffect(() => {
    const handleOpenEditor = (e) => setActiveEditor(e.detail);
    window.addEventListener('open-template-item-editor', handleOpenEditor);
    return () => window.removeEventListener('open-template-item-editor', handleOpenEditor);
  }, []);

  const saveItemContent = (newContent, newUrl) => {
    const updateItemInFolders = (folders) => {
      return folders.map(f => {
        if (f.id === activeEditor.folderId) {
          return {
            ...f,
            items: f.items.map(i => i.id === activeEditor.item.id ? { ...i, content: newContent, url: newUrl } : i)
          };
        }
        if (f.subfolders && f.subfolders.length > 0) {
          return { ...f, subfolders: updateItemInFolders(f.subfolders) };
        }
        return f;
      });
    };
    setBuilderData({
      ...builderData,
      folders: updateItemInFolders(builderData.folders)
    });
    setActiveEditor(null);
  };

  const addRootFolder = () => {
    setBuilderData({
      ...builderData,
      folders: [...builderData.folders, {
        id: Math.random().toString(),
        name: 'New Folder',
        items: [],
        subfolders: []
      }]
    });
  };

  const saveTemplate = async () => {
    try {
      const payload = {
        name: builderData.name,
        description: builderData.description,
        visibility: builderData.visibility,
        folder_data: builderData.folders
      };
      
      if (editingTemplateId) {
        await updateTemplate(orgSlug, editingTemplateId, payload);
        alert('Template updated successfully!');
      } else {
        await createTemplate(orgSlug, payload);
        alert('Template created successfully!');
      }
      setShowBuilder(false);
      setEditingTemplateId(null);
      setBuilderData({
        name: 'New Template',
        description: '',
        visibility: 'public',
        folders: []
      });
      fetchTemplates();
    } catch (err) {
      console.error(err);
      const errorMsg = err.response?.data ? JSON.stringify(err.response.data) : err.message;
      alert(`Error saving template: ${errorMsg}`);
    }
  };

  if (activeTemplateForWizard) {
    return (
      <div style={{ padding: '2rem', background: '#f8fafc', minHeight: '100vh', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {/* Wizard Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #e2e8f0', paddingBottom: '1rem' }}>
          <div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>Create Goal from Template</h2>
            <p style={{ color: '#64748b', fontSize: '0.9rem', margin: '0.25rem 0 0 0' }}>
              Template: <strong style={{ color: '#6366f1' }}>{activeTemplateForWizard.name}</strong>
            </p>
          </div>
          <button 
            onClick={() => setActiveTemplateForWizard(null)}
            style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', color: '#475569', padding: '0.5rem 1.25rem', borderRadius: '8px', fontWeight: 600, cursor: 'pointer' }}
          >
            Back to Templates
          </button>
        </div>

        {/* Wizard Layout Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '2rem', flex: 1 }}>
          
          {/* Left Column: Form & Placeholders */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            
            {/* Goal Metadata Card */}
            <div style={{ background: 'white', padding: '1.5rem', borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.02)' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#1e293b', marginTop: 0, marginBottom: '1rem', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.5rem' }}>
                Goal Details
              </h3>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.35rem', fontSize: '0.85rem', fontWeight: 600, color: '#475569' }}>Goal Title *</label>
                  <input 
                    type="text" 
                    value={wizardGoalData.title}
                    onChange={e => setWizardGoalData({ ...wizardGoalData, title: e.target.value })}
                    style={{ width: '100%', padding: '0.65rem', borderRadius: '6px', border: '1px solid #cbd5e1', outline: 'none', fontSize: '0.9rem' }}
                    placeholder="Enter Goal Title"
                    required
                  />
                </div>
                
                <div>
                  <label style={{ display: 'block', marginBottom: '0.35rem', fontSize: '0.85rem', fontWeight: 600, color: '#475569' }}>Goal Description</label>
                  <textarea 
                    value={wizardGoalData.description}
                    onChange={e => setWizardGoalData({ ...wizardGoalData, description: e.target.value })}
                    style={{ width: '100%', padding: '0.65rem', borderRadius: '6px', border: '1px solid #cbd5e1', outline: 'none', fontSize: '0.9rem', minHeight: '60px', resize: 'vertical' }}
                    placeholder="Describe this goal (optional)"
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
                  <div>
                    <label style={{ display: 'block', marginBottom: '0.35rem', fontSize: '0.85rem', fontWeight: 600, color: '#475569' }}>Due Date</label>
                    <input 
                      type="date" 
                      value={wizardGoalData.due_date}
                      onChange={e => setWizardGoalData({ ...wizardGoalData, due_date: e.target.value })}
                      style={{ width: '100%', padding: '0.65rem', borderRadius: '6px', border: '1px solid #cbd5e1', outline: 'none', fontSize: '0.9rem' }}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', marginBottom: '0.35rem', fontSize: '0.85rem', fontWeight: 600, color: '#475569' }}>Priority</label>
                    <select 
                      value={wizardGoalData.priority}
                      onChange={e => setWizardGoalData({ ...wizardGoalData, priority: e.target.value })}
                      style={{ width: '100%', padding: '0.65rem', borderRadius: '6px', border: '1px solid #cbd5e1', outline: 'none', fontSize: '0.9rem' }}
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ display: 'block', marginBottom: '0.35rem', fontSize: '0.85rem', fontWeight: 600, color: '#475569' }}>Timeframe</label>
                    <select 
                      value={wizardGoalData.timeframe}
                      onChange={e => setWizardGoalData({ ...wizardGoalData, timeframe: e.target.value })}
                      style={{ width: '100%', padding: '0.65rem', borderRadius: '6px', border: '1px solid #cbd5e1', outline: 'none', fontSize: '0.9rem' }}
                    >
                      <option value="quarterly">Quarterly</option>
                      <option value="monthly">Monthly</option>
                      <option value="yearly">Yearly</option>
                      <option value="custom">Custom</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            {/* Template Variables / Placeholders Card */}
            <div style={{ background: 'white', padding: '1.5rem', borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.02)', flex: 1, display: 'flex', flexDirection: 'column' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#1e293b', marginTop: 0, marginBottom: '1rem', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.5rem' }}>
                Placeholder Variables
              </h3>
              
              {wizardVariables.length === 0 ? (
                <div style={{ color: '#94a3b8', fontSize: '0.9rem', padding: '2rem 0', textAlign: 'center', flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  No placeholder variables (like {"{Client_Name}"}) detected in this template.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', overflowY: 'auto', flex: 1, maxHeight: '300px', paddingRight: '0.5rem' }}>
                  <p style={{ margin: 0, fontSize: '0.8rem', color: '#64748b' }}>
                    Define the values for the placeholders in the template. They will be auto-replaced throughout the created structure.
                  </p>
                  {wizardVariables.map(v => (
                    <div key={v}>
                      <label style={{ display: 'block', marginBottom: '0.35rem', fontSize: '0.85rem', fontWeight: 600, color: '#64748b', textTransform: 'capitalize' }}>
                        {v.replaceAll('_', ' ')}
                      </label>
                      <input 
                        type="text" 
                        value={wizardPlaceholders[v] || ''}
                        onChange={e => setWizardPlaceholders({ ...wizardPlaceholders, [v]: e.target.value })}
                        style={{ width: '100%', padding: '0.65rem', borderRadius: '6px', border: '1px solid #cbd5e1', outline: 'none', fontSize: '0.9rem' }}
                        placeholder={`Value for {${v}}`}
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            {/* Submit Action */}
            <div style={{ display: 'flex', gap: '1rem', marginTop: 'auto' }}>
              <button 
                onClick={async () => {
                  if (!wizardGoalData.title) {
                    alert('Please enter a goal title.');
                    return;
                  }
                  try {
                    setLoading(true);
                    const res = await createGoalFromTemplate(orgSlug, activeTemplateForWizard.id, {
                      goal_title: wizardGoalData.title,
                      goal_description: wizardGoalData.description,
                      due_date: wizardGoalData.due_date,
                      priority: wizardGoalData.priority,
                      timeframe: wizardGoalData.timeframe,
                      placeholders: wizardPlaceholders
                    });
                    
                    alert('Successfully created goal and applied template structure!');
                    setActiveTemplateForWizard(null);
                    
                    if (onApplyTemplate) {
                      onApplyTemplate(res.goal_id);
                    }
                  } catch (err) {
                    console.error(err);
                    const errorMsg = err.response?.data ? JSON.stringify(err.response.data) : err.message;
                    alert(`Error creating goal from template: ${errorMsg}`);
                  } finally {
                    setLoading(false);
                  }
                }}
                disabled={loading}
                style={{ flex: 1, padding: '0.75rem', background: '#10b981', color: 'white', border: 'none', borderRadius: '8px', fontWeight: 600, fontSize: '0.95rem', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}
              >
                {loading ? 'Creating Project Structure...' : 'Confirm & Create Project Structure'}
              </button>
            </div>

          </div>

          {/* Right Column: Live Interactive Preview */}
          <div style={{ background: 'white', padding: '1.5rem', borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.02)', display: 'flex', flexDirection: 'column' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#1e293b', marginTop: 0, marginBottom: '1rem', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.5rem' }}>
              Project Structure Preview (Live)
            </h3>
            
            <div style={{ flex: 1, overflowY: 'auto', background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              
              {/* Goal Title Node */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, color: '#0f172a', fontSize: '1.05rem', borderBottom: '1px dashed #cbd5e1', paddingBottom: '0.5rem' }}>
                <Target size={18} style={{ color: '#6366f1' }} />
                <span>{replacePlaceholders(wizardGoalData.title || 'Untitled Goal', wizardPlaceholders)}</span>
              </div>
              
              {/* Recursive Folder Preview tree */}
              {activeTemplateForWizard.folders && activeTemplateForWizard.folders.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  {activeTemplateForWizard.folders.filter(f => !f.parent).map(folder => (
                    <PreviewFolder key={folder.id} folder={folder} placeholderValues={wizardPlaceholders} />
                  ))}
                </div>
              ) : (
                <div style={{ color: '#94a3b8', fontSize: '0.85rem', textAlign: 'center', padding: '2rem 0' }}>
                  No folders or tasks in this template.
                </div>
              )}

            </div>
          </div>

        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '2rem', background: '#f8fafc', minHeight: '100vh' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>Template Library</h2>
          <p style={{ color: '#64748b', fontSize: '0.9rem', margin: '0.25rem 0 0 0' }}>Manage reusable folder structures and workflows</p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button 
            onClick={() => setShowImportModal(true)}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'white', color: '#475569', border: '1px solid #cbd5e1', padding: '0.6rem 1.25rem', borderRadius: '8px', fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s' }}
          >
            <FileSpreadsheet size={16} style={{ color: '#10b981' }} /> Import from CSV
          </button>
          <button 
            onClick={() => setShowBuilder(true)}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#6366f1', color: 'white', padding: '0.6rem 1.25rem', borderRadius: '8px', border: 'none', fontWeight: 600, cursor: 'pointer' }}
          >
            <Plus size={16} /> Create Template
          </button>
        </div>
      </div>

      {showBuilder ? (
        <div style={{ background: 'white', padding: '2rem', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
            <div style={{ flex: 1, marginRight: '2rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.75rem', padding: '0.15rem 0.5rem', background: editingTemplateId ? '#eff6ff' : '#f0fdf4', color: editingTemplateId ? '#2563eb' : '#16a34a', borderRadius: '9999px', fontWeight: 600, border: `1px solid ${editingTemplateId ? '#bfdbfe' : '#bbf7d0'}` }}>
                  {editingTemplateId ? 'Editing Template' : 'New Template'}
                </span>
              </div>
              <input 
                type="text" 
                value={builderData.name}
                onChange={(e) => setBuilderData({...builderData, name: e.target.value})}
                style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0f172a', border: 'none', borderBottom: '2px solid transparent', padding: '0.25rem 0', width: '100%', outline: 'none' }}
                onFocus={(e) => e.target.style.borderBottom = '2px solid #6366f1'}
                onBlur={(e) => e.target.style.borderBottom = '2px solid transparent'}
                placeholder="Template Name"
              />
              <input 
                type="text" 
                value={builderData.description}
                onChange={(e) => setBuilderData({...builderData, description: e.target.value})}
                style={{ fontSize: '0.95rem', color: '#64748b', border: 'none', padding: '0.25rem 0', width: '100%', outline: 'none', marginTop: '0.5rem' }}
                placeholder="Add a short description..."
              />
            </div>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <select 
                value={builderData.visibility} 
                onChange={(e) => setBuilderData({...builderData, visibility: e.target.value})}
                style={{ padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1', outline: 'none' }}
              >
                <option value="public">Organization Public</option>
                <option value="private">Personal Only</option>
              </select>
              <button 
                onClick={saveTemplate}
                style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#10b981', color: 'white', padding: '0.5rem 1rem', borderRadius: '6px', border: 'none', fontWeight: 600, cursor: 'pointer' }}
              >
                <Save size={16} /> Save Template
              </button>
              <button 
                onClick={handleCancelBuilder}
                style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#f1f5f9', color: '#475569', padding: '0.5rem 1rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontWeight: 600, cursor: 'pointer' }}
              >
                Cancel
              </button>
            </div>
          </div>

          <div style={{ background: '#f8fafc', padding: '1.5rem', borderRadius: '8px', border: '1px solid #e2e8f0', minHeight: '300px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#334155', margin: 0 }}>Structure</h3>
              <button 
                onClick={addRootFolder}
                style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', background: 'white', color: '#6366f1', padding: '0.4rem 0.75rem', borderRadius: '6px', border: '1px solid #c7d2fe', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer' }}
              >
                <Folder size={14} /> Add Root Folder
              </button>
            </div>

            {builderData.folders.length === 0 ? (
              <div style={{ textAlign: 'center', color: '#94a3b8', padding: '3rem 0', fontSize: '0.9rem' }}>
                <Folder size={48} style={{ opacity: 0.3, marginBottom: '1rem' }} />
                <p>No folders added yet. Create a folder to start organizing items.</p>
              </div>
            ) : (
              <div style={{ marginTop: '1.5rem' }}>
                {builderData.folders.map(folder => (
                  <FolderItem 
                    key={folder.id} 
                    folder={folder} 
                    updateFolder={(updated) => setBuilderData({
                      ...builderData,
                      folders: builderData.folders.map(f => f.id === folder.id ? updated : f)
                    })}
                    deleteFolder={() => setBuilderData({
                      ...builderData,
                      folders: builderData.folders.filter(f => f.id !== folder.id)
                    })}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
          {templates.length === 0 ? (
            <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '4rem', background: 'white', borderRadius: '12px', border: '1px dashed #cbd5e1', color: '#64748b' }}>
              <FileText size={48} style={{ opacity: 0.3, marginBottom: '1rem' }} />
              <h3>No Templates Found</h3>
              <p>Create your first template to standardize your workflows.</p>
            </div>
          ) : (
            templates.map(template => (
              <div key={template.id} style={{ background: 'white', padding: '1.5rem', borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.02)', position: 'relative' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#1e293b', margin: '0 0 0.25rem 0' }}>{template.name}</h3>
                    <p style={{ fontSize: '0.8rem', color: '#64748b', margin: 0 }}>
                      {template.description || 'No description provided'}
                    </p>
                  </div>
                  <span style={{ fontSize: '0.7rem', padding: '0.2rem 0.5rem', background: template.visibility === 'public' ? '#ecfdf5' : '#f1f5f9', color: template.visibility === 'public' ? '#059669' : '#475569', borderRadius: '4px', border: `1px solid ${template.visibility === 'public' ? '#a7f3d0' : '#e2e8f0'}`, fontWeight: 600 }}>
                    {template.visibility === 'public' ? 'Public' : 'Personal'}
                  </span>
                </div>
                
                <div style={{ marginTop: '1.5rem', display: 'flex', gap: '0.5rem' }}>
                  <button 
                    onClick={() => openTemplateWizard(template)} 
                    style={{ flex: 2, padding: '0.5rem', background: '#6366f1', color: 'white', border: 'none', borderRadius: '6px', fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.35rem' }}
                  >
                    Use Template
                  </button>
                  <button 
                    onClick={() => handleEditTemplate(template)} 
                    title="Edit Template"
                    style={{ flex: '0 0 auto', width: '36px', height: '36px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: '6px', color: '#475569', cursor: 'pointer', transition: 'all 0.2s' }}
                  >
                    <Edit2 size={14} />
                  </button>
                  <button 
                    onClick={() => handleDeleteTemplate(template.id, template.name)} 
                    title="Delete Template"
                    style={{ flex: '0 0 auto', width: '36px', height: '36px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#fef2f2', border: '1px solid #fee2e2', borderRadius: '6px', color: '#ef4444', cursor: 'pointer', transition: 'all 0.2s' }}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Item Editor Modal */}
      {activeEditor && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ background: 'white', padding: '2rem', borderRadius: '12px', width: '500px', maxWidth: '90%' }}>
            <h3 style={{ marginTop: 0, marginBottom: '1.5rem', fontSize: '1.25rem' }}>
              Edit {activeEditor.item.name}
            </h3>
            
            {activeEditor.item.item_type === 'link' ? (
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 600 }}>URL Address</label>
                <input 
                  type="url" 
                  defaultValue={activeEditor.item.url || ''}
                  id="item-url-input"
                  style={{ width: '100%', padding: '0.75rem', borderRadius: '6px', border: '1px solid #cbd5e1', marginBottom: '1rem' }}
                  placeholder="https://example.com"
                />
              </div>
            ) : activeEditor.item.item_type === 'task_list' || activeEditor.item.item_type === 'checklist' ? (
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 600 }}>List Items (One per line)</label>
                <textarea 
                  defaultValue={(activeEditor.item.content?.items || []).join('\n')}
                  id="item-content-input"
                  style={{ width: '100%', padding: '0.75rem', borderRadius: '6px', border: '1px solid #cbd5e1', minHeight: '150px', resize: 'vertical' }}
                  placeholder="Task 1&#10;Task 2&#10;Task 3"
                />
              </div>
            ) : activeEditor.item.item_type === 'task' ? (
              <div>
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 600 }}>Task Description</label>
                  <textarea 
                    defaultValue={activeEditor.item.content?.description || ''}
                    id="task-desc-input"
                    style={{ width: '100%', padding: '0.75rem', borderRadius: '6px', border: '1px solid #cbd5e1', minHeight: '80px', resize: 'vertical' }}
                    placeholder="Enter task description..."
                  />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                  <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 600 }}>Estimated Hours</label>
                    <input 
                      type="number" 
                      step="0.5"
                      defaultValue={activeEditor.item.content?.estimated_hours || ''}
                      id="task-hours-input"
                      style={{ width: '100%', padding: '0.75rem', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                      placeholder="e.g. 4.5"
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 600 }}>Priority</label>
                    <select 
                      defaultValue={activeEditor.item.content?.priority || 'medium'}
                      id="task-priority-input"
                      style={{ width: '100%', padding: '0.75rem', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 600 }}>Assignee Roles or Emails (comma-separated)</label>
                  <input 
                    type="text" 
                    defaultValue={(activeEditor.item.content?.assignees || []).join(', ')}
                    id="task-assignees-input"
                    style={{ width: '100%', padding: '0.75rem', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                    placeholder="owner, created_by, test@example.com"
                  />
                  <small style={{ color: '#94a3b8', fontSize: '0.75rem', marginTop: '0.25rem', display: 'block' }}>
                    Use 'owner' for goal owner, 'created_by' for yourself, or user email addresses.
                  </small>
                </div>
              </div>
            ) : (
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 600 }}>Document Content</label>
                <textarea 
                  defaultValue={activeEditor.item.content?.text || ''}
                  id="item-content-input"
                  style={{ width: '100%', padding: '0.75rem', borderRadius: '6px', border: '1px solid #cbd5e1', minHeight: '200px', resize: 'vertical' }}
                  placeholder="Start writing..."
                />
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1.5rem' }}>
              <button 
                onClick={() => setActiveEditor(null)}
                style={{ padding: '0.5rem 1rem', background: '#f1f5f9', border: 'none', borderRadius: '6px', fontWeight: 600, cursor: 'pointer' }}
              >
                Cancel
              </button>
              <button 
                onClick={() => {
                  let newContent = {};
                  let newUrl = activeEditor.item.url || '';
                  
                  if (activeEditor.item.item_type === 'link') {
                    newUrl = document.getElementById('item-url-input').value;
                  } else if (activeEditor.item.item_type === 'task_list' || activeEditor.item.item_type === 'checklist') {
                    const text = document.getElementById('item-content-input').value;
                    newContent = { items: text.split('\n').filter(t => t.trim()) };
                  } else if (activeEditor.item.item_type === 'task') {
                    const desc = document.getElementById('task-desc-input').value;
                    const hours = parseFloat(document.getElementById('task-hours-input').value) || null;
                    const priority = document.getElementById('task-priority-input').value;
                    const assigneesRaw = document.getElementById('task-assignees-input').value;
                    const assignees = assigneesRaw.split(',').map(a => a.trim()).filter(a => a);
                    newContent = { description: desc, estimated_hours: hours, priority, assignees };
                  } else {
                    newContent = { text: document.getElementById('item-content-input').value };
                  }
                  
                  saveItemContent(newContent, newUrl);
                }}
                style={{ padding: '0.5rem 1rem', background: '#6366f1', color: 'white', border: 'none', borderRadius: '6px', fontWeight: 600, cursor: 'pointer' }}
              >
                Save Content
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Import Modal */}
      {showImportModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(15, 23, 42, 0.6)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ background: 'white', padding: '2rem', borderRadius: '16px', width: parsedData ? '850px' : '500px', maxWidth: '95%', maxHeight: '90vh', display: 'flex', flexDirection: 'column', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)', border: '1px solid #e2e8f0', transition: 'all 0.3s ease' }}>
            
            {/* Modal Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', borderBottom: '1px solid #f1f5f9', paddingBottom: '1rem' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <FileSpreadsheet size={20} style={{ color: '#10b981' }} />
                  {parsedData ? 'Review and Adjust Template' : 'Import Template from CSV / Excel'}
                </h3>
                <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.8rem', color: '#64748b' }}>
                  {parsedData ? 'Verify the parsed rows and details before loading them into the template builder.' : 'Upload a spreadsheet containing goals, folders, files, and tasks.'}
                </p>
              </div>
              <button 
                onClick={() => {
                  setShowImportModal(false);
                  setImportFile(null);
                  setParsedData(null);
                  setImportError(null);
                }} 
                style={{ background: 'none', border: 'none', fontSize: '1.5rem', color: '#94a3b8', cursor: 'pointer' }}
              >
                &times;
              </button>
            </div>

            {/* Modal Body */}
            <div style={{ flex: 1, overflowY: 'auto', marginBottom: '1.5rem', paddingRight: '0.5rem' }}>
              {!parsedData ? (
                // Step 1: Upload File
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                  
                  {/* File Dropzone */}
                  <div 
                    onDragOver={handleDragOver}
                    onDrop={handleDrop}
                    onClick={() => document.getElementById('file-upload-input').click()}
                    style={{
                      border: '2px dashed #cbd5e1',
                      borderRadius: '12px',
                      padding: '2.5rem 1.5rem',
                      textAlign: 'center',
                      cursor: 'pointer',
                      background: importFile ? '#f0fdf4' : '#f8fafc',
                      borderColor: importFile ? '#86efac' : '#cbd5e1',
                      transition: 'all 0.2s ease',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '0.75rem'
                    }}
                  >
                    <input 
                      type="file" 
                      id="file-upload-input" 
                      accept=".csv, .xlsx, .xls"
                      onChange={handleFileChange}
                      style={{ display: 'none' }}
                    />
                    <Upload size={40} style={{ color: importFile ? '#10b981' : '#64748b' }} />
                    <div>
                      <p style={{ margin: 0, fontSize: '0.95rem', fontWeight: 600, color: '#334155' }}>
                        {importFile ? importFile.name : 'Click to upload or drag & drop'}
                      </p>
                      <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.8rem', color: '#64748b' }}>
                        Supports CSV (.csv) and Excel (.xlsx, .xls)
                      </p>
                    </div>
                    {importFile && (
                      <span style={{ fontSize: '0.75rem', padding: '0.2rem 0.6rem', background: '#dcfce7', color: '#166534', borderRadius: '9999px', fontWeight: 600 }}>
                        File Selected ({(importFile.size / 1024).toFixed(1)} KB)
                      </span>
                    )}
                  </div>

                  {/* Instructions/CSV Format Box */}
                  <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '10px', padding: '1rem', display: 'flex', gap: '0.75rem' }}>
                    <AlertCircle size={20} style={{ color: '#2563eb', flexShrink: 0, marginTop: '0.1rem' }} />
                    <div>
                      <h4 style={{ margin: '0 0 0.4rem 0', fontSize: '0.85rem', fontWeight: 600, color: '#1e3a8a' }}>Required Spreadsheet Columns:</h4>
                      <p style={{ margin: 0, fontSize: '0.8rem', color: '#1e40af', fontFamily: 'monospace', wordBreak: 'break-all' }}>
                        Goal_Title, Folder_Name, Document_Name, Document_Content, Task_Title, Task_Description, Est_Hours, Assignee_Email, Priority, Impact, Risk
                      </p>
                      <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.75rem', color: '#1e40af' }}>
                        💡 Use <code>/</code> or <code>&gt;</code> in <code>Folder_Name</code> for nested subfolders (e.g. <code>Phase 1 &gt; Setup</code>).
                      </p>
                    </div>
                  </div>

                  {/* Progress Indicator */}
                  {importProgress !== null && (
                    <div style={{ marginTop: '0.5rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#475569', marginBottom: '0.25rem', fontWeight: 600 }}>
                        <span>Parsing File...</span>
                        <span>{importProgress}%</span>
                      </div>
                      <div style={{ width: '100%', height: '8px', background: '#e2e8f0', borderRadius: '9999px', overflow: 'hidden' }}>
                        <div style={{ width: `${importProgress}%`, height: '100%', background: '#10b981', transition: 'width 0.2s ease', borderRadius: '9999px' }} />
                      </div>
                    </div>
                  )}

                  {/* Error Alert */}
                  {importError && (
                    <div style={{ background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: '8px', padding: '0.75rem 1rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                      <AlertCircle size={16} style={{ color: '#ef4444', flexShrink: 0 }} />
                      <span style={{ fontSize: '0.85rem', color: '#991b1b', fontWeight: 500 }}>{importError}</span>
                    </div>
                  )}

                </div>
              ) : (
                // Step 2: Preview parsed data
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  
                  {/* Template Meta fields */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 2fr', gap: '1rem' }}>
                    <div>
                      <label style={{ display: 'block', marginBottom: '0.35rem', fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>Template Name</label>
                      <input 
                        type="text" 
                        value={editedGoalTitle}
                        onChange={e => setEditedGoalTitle(e.target.value)}
                        style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid #cbd5e1', outline: 'none', fontSize: '0.85rem' }}
                        placeholder="Template Name"
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', marginBottom: '0.35rem', fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>Template Description</label>
                      <input 
                        type="text" 
                        value={editedTemplateDescription}
                        onChange={e => setEditedTemplateDescription(e.target.value)}
                        style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid #cbd5e1', outline: 'none', fontSize: '0.85rem' }}
                        placeholder="Description of this template"
                      />
                    </div>
                  </div>

                  {/* Summary / Stats */}
                  <div style={{ display: 'flex', gap: '1rem', background: '#f8fafc', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '0.8rem', color: '#475569' }}>
                    <div>📊 Rows found: <strong>{parsedData.rows?.length || 0}</strong></div>
                    <div style={{ borderLeft: '1px solid #cbd5e1', paddingLeft: '1rem' }}>📂 Tree representation ready to load</div>
                  </div>

                  {/* Table Preview */}
                  <div style={{ border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden', background: '#ffffff', maxHeight: '350px', overflowY: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
                      <thead style={{ background: '#f1f5f9', color: '#475569', position: 'sticky', top: 0, zIndex: 10, borderBottom: '1px solid #e2e8f0' }}>
                        <tr>
                          <th style={{ padding: '0.6rem 0.75rem', fontWeight: 600 }}>Goal Title</th>
                          <th style={{ padding: '0.6rem 0.75rem', fontWeight: 600 }}>Folder Path</th>
                          <th style={{ padding: '0.6rem 0.75rem', fontWeight: 600 }}>Document (Content)</th>
                          <th style={{ padding: '0.6rem 0.75rem', fontWeight: 600 }}>Task Title (Hours, Pri)</th>
                          <th style={{ padding: '0.6rem 0.75rem', fontWeight: 600 }}>Assignee</th>
                        </tr>
                      </thead>
                      <tbody>
                        {parsedData.rows?.map((row, idx) => {
                          const goal = row.Goal_Title || '';
                          const folder = row.Folder_Name || '';
                          const docName = row.Document_Name || '';
                          const docContent = row.Document_Content || '';
                          const taskTitle = row.Task_Title || '';
                          const taskDesc = row.Task_Description || '';
                          const estHours = row.Est_Hours || '';
                          const priority = row.Priority || '';
                          const email = row.Assignee_Email || '';

                          return (
                            <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9', background: idx % 2 === 0 ? '#ffffff' : '#f8fafc' }}>
                              <td style={{ padding: '0.5rem 0.75rem', color: '#334155', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '140px' }} title={goal}>{goal}</td>
                              <td style={{ padding: '0.5rem 0.75rem', color: '#6366f1', fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '140px' }} title={folder}>{folder}</td>
                              <td style={{ padding: '0.5rem 0.75rem', color: '#475569', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '180px' }} title={docContent}>
                                {docName ? (
                                  <span>📄 {docName} <span style={{ color: '#94a3b8', fontSize: '0.75rem' }}>({docContent ? `${docContent.slice(0, 20)}...` : 'empty'})</span></span>
                                ) : '-'}
                              </td>
                              <td style={{ padding: '0.5rem 0.75rem', color: '#334155', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '180px' }} title={taskDesc}>
                                {taskTitle ? (
                                  <span>
                                    ✅ {taskTitle}{' '}
                                    <span style={{ color: '#94a3b8', fontSize: '0.75rem' }}>
                                      ({estHours ? `${estHours}h` : ''}{estHours && priority ? ', ' : ''}{priority || ''})
                                    </span>
                                  </span>
                                ) : '-'}
                              </td>
                              <td style={{ padding: '0.5rem 0.75rem', color: '#475569', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '120px' }} title={email}>{email || '-'}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', borderTop: '1px solid #f1f5f9', paddingTop: '1rem' }}>
              <button 
                onClick={() => {
                  setShowImportModal(false);
                  setImportFile(null);
                  setParsedData(null);
                  setImportError(null);
                }} 
                style={{ padding: '0.5rem 1rem', background: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '6px', fontWeight: 600, color: '#475569', cursor: 'pointer' }}
              >
                Cancel
              </button>
              
              {!parsedData ? (
                <button 
                  onClick={handleUpload}
                  disabled={!importFile || importProgress !== null}
                  style={{ 
                    padding: '0.5rem 1.25rem', 
                    background: importFile && importProgress === null ? '#10b981' : '#cbd5e1', 
                    color: 'white', 
                    border: 'none', 
                    borderRadius: '6px', 
                    fontWeight: 600, 
                    cursor: importFile && importProgress === null ? 'pointer' : 'not-allowed',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.35rem'
                  }}
                >
                  {importProgress !== null ? 'Uploading...' : 'Upload & Parse'}
                </button>
              ) : (
                <button 
                  onClick={handleLoadIntoBuilder}
                  style={{ padding: '0.5rem 1.25rem', background: '#6366f1', color: 'white', border: 'none', borderRadius: '6px', fontWeight: 600, cursor: 'pointer' }}
                >
                  Load into Builder
                </button>
              )}
            </div>

          </div>
        </div>
      )}
    </div>
  );
};

export default TemplateManager;
