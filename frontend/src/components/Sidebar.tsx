import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  UploadCloud, 
  FlaskConical, 
  GitCompare, 
  BookOpen, 
  Workflow, 
  Cpu, 
  FileText, 
  Settings 
} from 'lucide-react';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/upload', label: 'Upload & Analyze', icon: UploadCloud },
  { path: '/experiments', label: 'Experiments', icon: FlaskConical },
  { path: '/compare', label: 'Compare Runs', icon: GitCompare },
  { path: '/rag', label: 'RAG Knowledge', icon: BookOpen },
  { path: '/workflows', label: 'Agent Workflows', icon: Workflow },
  { path: '/mcp', label: 'MCP Hub', icon: Cpu },
  { path: '/reports', label: 'Reports', icon: FileText },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col min-h-screen border-r border-slate-800">
      <div className="p-6 border-b border-slate-800 flex items-center space-x-3">
        <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white text-xl shadow-md shadow-indigo-500/30">
          LT
        </div>
        <div>
          <h1 className="font-semibold text-white tracking-wide text-lg">LabTrace</h1>
          <p className="text-xs text-slate-400">AI Reproducibility Platform</p>
        </div>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-indigo-600/20 text-indigo-400 border-l-2 border-indigo-500'
                  : 'hover:bg-slate-800 text-slate-400 hover:text-slate-200'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-slate-800 text-xs text-slate-500 text-center">
        LabTrace v1.0.0 &bull; Local & Azure Ready
      </div>
    </aside>
  );
};
