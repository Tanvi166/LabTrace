import React from 'react';
import { useAuth } from '../context/AuthContext';
import { User as UserIcon, LogOut, Cloud, HardDrive } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <header className="h-16 glass-panel border-b border-t-0 border-x-0 rounded-none px-8 flex items-center justify-between sticky top-0 z-20">
      <div className="flex items-center space-x-4">
        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-white/5 text-slate-300 border border-white/10 shadow-glass">
          <HardDrive className="w-3.5 h-3.5 mr-1 text-neon-cyan" />
          Local Mode Active
        </span>
        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-brand-500/20 text-brand-300 border border-brand-500/30 shadow-neon">
          <Cloud className="w-3.5 h-3.5 mr-1" />
          Azure Config Ready
        </span>
      </div>
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-r from-neon-purple to-brand-500 text-white flex items-center justify-center font-medium text-sm shadow-neon">
            {user?.full_name?.charAt(0) || 'R'}
          </div>
          <div className="text-sm">
            <p className="font-medium text-white leading-none">{user?.full_name || 'Researcher'}</p>
            <p className="text-xs text-brand-300 mt-0.5">{user?.email || 'researcher@labtrace.ai'}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="text-slate-400 hover:text-neon-cyan transition-colors p-1 hover:shadow-neon rounded-full"
          title="Log out"
        >
          <LogOut className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
};
