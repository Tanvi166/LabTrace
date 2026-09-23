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
    <aside className="w-64 glass-panel border-r-0 rounded-r-none flex flex-col min-h-screen relative z-10">
      <div className="p-6 border-b border-white/10 flex items-center space-x-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center font-bold text-white text-xl shadow-neon">
          LT
        </div>
        <div>
          <h1 className="font-semibold text-white tracking-wide text-lg text-glow">LabTrace</h1>
          <p className="text-xs text-brand-400">AI Reproducibility</p>
        </div>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-300 ${
                isActive
                  ? 'bg-brand-500/20 text-brand-400 shadow-[inset_4px_0_0_0_#3b82f6] shadow-neon'
                  : 'hover:bg-white/5 text-slate-400 hover:text-white'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-white/10 text-xs text-slate-500 text-center">
        LabTrace v1.0.0 &bull; Local & Azure
      </div>
    </aside>
  );
};
