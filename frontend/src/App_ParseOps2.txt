import React, { useState } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { Sidebar } from './components/Sidebar';
import { Modal } from './components/Modal';
import { showToast } from './components/Toast';
import { apiClient } from './api/client';
import { Toaster } from 'sonner';

// Page Imports
import { AuthPage } from './pages/AuthPage';
import { Dashboard } from './pages/Dashboard';
import { Tasks } from './pages/Tasks';
import { Goals } from './pages/Goals';
import { Chat } from './pages/Chat';
import { Analytics } from './pages/Analytics';
import { CSVImport } from './pages/CSVImport';
import { Profile } from './pages/Profile';
import { Building, Plus, RefreshCw } from 'lucide-react';

// Guard for Authenticated Pages
const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, organizations, isLoading, fetchUserOrganizations, logout } = useAuth();
  const location = useLocation();

  // Workspace creation fallback
  const [isWorkspaceModalOpen, setIsWorkspaceModalOpen] = useState(false);
  const [workspaceName, setWorkspaceName] = useState('');
  const [workspaceDesc, setWorkspaceDesc] = useState('');
  const [isCreatingWorkspace, setIsCreatingWorkspace] = useState(false);

  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <RefreshCw className="animate-spin text-indigo-500" size={32} />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/auth" state={{ from: location }} replace />;
  }

  const handleCreateWorkspace = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!workspaceName.trim()) return;
    setIsCreatingWorkspace(true);
    try {
      await apiClient.post('/api/organizations/', {
        name: workspaceName,
        description: workspaceDesc,
      });
      showToast('success', 'Workspace Created', `Successfully created your workspace '${workspaceName}'.`);
      setIsWorkspaceModalOpen(false);
      setWorkspaceName('');
      setWorkspaceDesc('');
      await fetchUserOrganizations();
    } catch (err) {
      showToast('error', 'Error', 'Failed to create workspace.');
    } finally {
      setIsCreatingWorkspace(false);
    }
  };

  // If user has no workspaces, force workspace creation
  if (organizations.length === 0) {
    return (
      <div className="h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 px-4">
        <div className="max-w-md w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8 shadow-xl text-center space-y-6">
          <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 text-indigo-500 flex items-center justify-center mx-auto">
            <Building size={32} />
          </div>
          <div className="space-y-2">
            <h2 className="text-xl font-display font-bold text-slate-800 dark:text-slate-100">Setup your Workspace</h2>
            <p className="text-sm text-slate-400">
              You are not a member of any workspace yet. To begin collaborating, create your initial workspace.
            </p>
          </div>
          
          <form onSubmit={handleCreateWorkspace} className="space-y-4 text-left">
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Workspace Name
              </label>
              <input
                type="text"
                required
                value={workspaceName}
                onChange={(e) => setWorkspaceName(e.target.value)}
                placeholder="e.g. engineering-team"
                className="w-full px-3.5 py-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-transparent text-slate-800 dark:text-slate-200 text-sm outline-none focus:border-indigo-500 transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Workspace Description
              </label>
              <input
                type="text"
                value={workspaceDesc}
                onChange={(e) => setWorkspaceDesc(e.target.value)}
                placeholder="e.g. Sprints and OKRs board"
                className="w-full px-3.5 py-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-transparent text-slate-800 dark:text-slate-200 text-sm outline-none focus:border-indigo-500 transition-colors"
              />
            </div>

            <button
              type="submit"
              disabled={isCreatingWorkspace || !workspaceName}
              className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold flex items-center justify-center gap-1.5 shadow-lg shadow-indigo-600/20 cursor-pointer disabled:opacity-75"
            >
              {isCreatingWorkspace ? <RefreshCw className="animate-spin" size={16} /> : <Plus size={16} />}
              <span>Create Workspace</span>
            </button>

            <button
              type="button"
              onClick={logout}
              className="w-full mt-2 py-2.5 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 text-sm font-semibold flex items-center justify-center cursor-pointer transition-colors"
            >
              <span>Sign Out</span>
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex bg-slate-50 dark:bg-slate-950 overflow-hidden">
      <Sidebar />
      <main className="flex-1 h-full overflow-hidden relative">
        {children}
      </main>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <>
      <Toaster richColors position="top-right" theme="system" closeButton />
      <Routes>
        {/* Public Pages */}
        <Route path="/auth" element={<AuthPage />} />
        <Route path="/login" element={<Navigate to="/auth" replace />} />
        <Route path="/register" element={<Navigate to="/auth" replace />} />

        {/* Private Authenticated Pages */}
        <Route
          path="/"
          element={
            <AppLayout>
              <Dashboard />
            </AppLayout>
          }
        />
        <Route
          path="/tasks"
          element={
            <AppLayout>
              <Tasks />
            </AppLayout>
          }
        />
        <Route
          path="/goals"
          element={
            <AppLayout>
              <Goals />
            </AppLayout>
          }
        />
        <Route
          path="/chat"
          element={
            <AppLayout>
              <Chat />
            </AppLayout>
          }
        />
        <Route
          path="/analytics"
          element={
            <AppLayout>
              <Analytics />
            </AppLayout>
          }
        />
        <Route
          path="/import"
          element={
            <AppLayout>
              <CSVImport />
            </AppLayout>
          }
        />
        <Route
          path="/profile"
          element={
            <AppLayout>
              <Profile />
            </AppLayout>
          }
        />

        {/* Catch All Redirect */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
};

export default App;
