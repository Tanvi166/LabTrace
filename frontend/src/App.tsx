import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import { Sidebar } from './components/Sidebar';
import { Navbar } from './components/Navbar';

import { DashboardPage } from './pages/DashboardPage';
import { UploadPage } from './pages/UploadPage';
import { ExperimentDetailPage } from './pages/ExperimentDetailPage';
import { ComparePage } from './pages/ComparePage';
import { RagPage } from './pages/RagPage';
import { WorkflowsPage } from './pages/WorkflowsPage';
import { McpPage } from './pages/McpPage';
import { ReportsPage } from './pages/ReportsPage';
import { SettingsPage } from './pages/SettingsPage';

const queryClient = new QueryClient();

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <div className="flex min-h-screen bg-transparent text-slate-200">
            <Sidebar />
            <div className="flex-1 flex flex-col min-w-0">
              <Navbar />
              <main className="flex-1 p-8 overflow-y-auto">
                <Routes>
                  <Route path="/" element={<DashboardPage />} />
                  <Route path="/upload" element={<UploadPage />} />
                  <Route path="/experiments/:id" element={<ExperimentDetailPage />} />
                  <Route path="/compare" element={<ComparePage />} />
                  <Route path="/rag" element={<RagPage />} />
                  <Route path="/workflows" element={<WorkflowsPage />} />
                  <Route path="/mcp" element={<McpPage />} />
                  <Route path="/reports" element={<ReportsPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                </Routes>
              </main>
            </div>
          </div>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
