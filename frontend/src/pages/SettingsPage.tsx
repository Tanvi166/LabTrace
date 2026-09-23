import React, { useState } from 'react';
import { ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('AI Configuration');
  const navigate = useNavigate();

  return (
    <div className="space-y-6 max-w-3xl pb-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white mb-2">Settings</h1>
        <p className="text-sm text-slate-400">Configure your environment and integrations.</p>
      </div>

      {/* Tabs */}
      <div className="flex items-center space-x-6 border-b border-slate-700/50 mb-6">
        {['AI Configuration', 'MCP', 'Account'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-3 text-sm font-semibold transition-colors relative ${
              activeTab === tab ? 'text-white' : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            {tab}
            {activeTab === tab && (
              <span className="absolute bottom-[-1px] left-0 w-full h-[2px] bg-brand-400 shadow-[0_0_10px_rgba(45,212,191,0.5)]"></span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'AI Configuration' && (
        <div className="space-y-6">
          
          {/* Azure Services Card */}
          <div className="glass-panel p-6">
            <h2 className="text-base font-semibold text-white mb-6">Azure Services</h2>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-slate-300 text-sm font-medium">Azure Foundry</span>
                <div className="flex items-center">
                  <div className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)] mr-2"></div>
                  <span className="text-emerald-400 text-sm font-semibold">Connected</span>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-slate-300 text-sm font-medium">Azure AI Search</span>
                <div className="flex items-center">
                  <div className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)] mr-2"></div>
                  <span className="text-emerald-400 text-sm font-semibold">Connected</span>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-slate-300 text-sm font-medium">Azure OpenAI</span>
                <div className="flex items-center">
                  <div className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)] mr-2"></div>
                  <span className="text-emerald-400 text-sm font-semibold">Connected</span>
                </div>
              </div>
            </div>
          </div>

          {/* MCP Server Card */}
          <div className="glass-panel p-6">
            <h2 className="text-base font-semibold text-white mb-6">MCP Server</h2>
            
            <div className="space-y-4 mb-8">
              <div className="flex items-center justify-between">
                <span className="text-slate-300 text-sm font-medium">Status</span>
                <div className="flex items-center">
                  <div className="w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.8)] mr-2"></div>
                  <span className="text-cyan-400 text-sm font-semibold">Running</span>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-slate-300 text-sm font-medium">Tools Available</span>
                <span className="text-white text-sm font-semibold">4</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-slate-300 text-sm font-medium">Recent Calls</span>
                <span className="text-white text-sm font-semibold">12</span>
              </div>
            </div>
            
            <div className="flex justify-end">
              <button 
                onClick={() => navigate('/mcp')}
                className="px-5 py-2.5 rounded-xl border border-sky-500/30 bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 text-sm font-semibold transition-colors flex items-center shadow-inner"
              >
                View MCP Tools <ArrowRight className="w-4 h-4 ml-2" />
              </button>
            </div>
          </div>

        </div>
      )}

      {activeTab !== 'AI Configuration' && (
        <div className="glass-panel p-12 text-center text-slate-500 text-sm">
          Content for {activeTab} is not yet available.
        </div>
      )}
    </div>
  );
};
