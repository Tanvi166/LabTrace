import React from 'react';
import { useAuth } from '../context/AuthContext';
import { User as UserIcon, LogOut, Cloud, HardDrive } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-8 flex items-center justify-between shadow-sm">
      <div className="flex items-center space-x-4">
        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
          <HardDrive className="w-3.5 h-3.5 mr-1" />
          Local Mode Active
        </span>
        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
          <Cloud className="w-3.5 h-3.5 mr-1" />
          Azure Config Ready
        </span>
      </div>
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-medium text-sm">
            {user?.full_name?.charAt(0) || 'R'}
          </div>
          <div className="text-sm">
            <p className="font-medium text-slate-800 leading-none">{user?.full_name || 'Researcher'}</p>
            <p className="text-xs text-slate-500 mt-0.5">{user?.email || 'researcher@labtrace.ai'}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="text-slate-400 hover:text-slate-600 transition-colors p-1"
          title="Log out"
        >
          <LogOut className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
};
