import React, { useEffect, useState } from 'react';
import { Cpu, Loader2, AlertCircle, Wrench, Activity, CheckCircle2 } from 'lucide-react';
import { experimentApi } from '../services/api';

export const McpPage: React.FC = () => {
  const [status, setStatus] = useState<any>(null);
  const [tools, setTools] = useState<any[]>([]);
  const [calls, setCalls] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      experimentApi.getMcpStatus(),
      experimentApi.getMcpTools(),
      experimentApi.getMcpCalls()
    ]).then(([s, t, c]) => {
      setStatus(s);
      setTools(t);
      setCalls(c);
    }).catch((err: any) => setError(err.response?.data?.detail || 'Unable to load MCP status'));
  }, []);

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white mb-2">MCP Server Hub</h1>
        <p className="text-sm text-slate-400">Model Context Protocol tools & connection status for Claude, Cursor, and Gemini.</p>
      </div>

      {error && (
        <div className="p-4 bg-red-900/20 border border-red-500/30 text-red-400 rounded-xl text-sm flex items-center">
          <AlertCircle className="w-5 h-5 mr-3" />
          {error}
        </div>
      )}

      {/* Status Card */}
      <div className="glass-panel p-6">
        <div className="flex items-center space-x-3 mb-6">
          <div className="p-2 rounded-xl bg-brand-500/20 border border-brand-500/30 text-brand-400 shadow-lg shadow-brand-500/10">
            <Cpu className="w-5 h-5" />
          </div>
          <h3 className="text-lg font-semibold text-white">MCP service status</h3>
        </div>

        {!status && !error ? (
          <div className="flex items-center text-slate-400">
            <Loader2 className="w-5 h-5 animate-spin mr-3 text-brand-400" />
            Connecting to MCP Server...
          </div>
        ) : status && (
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center px-4 py-2.5 rounded-xl bg-slate-800/60 border border-slate-700/50 shadow-inner">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2" />
              <span className="text-sm font-semibold text-slate-300 capitalize">{status.status}</span>
            </div>
            <div className="flex items-center px-4 py-2.5 rounded-xl bg-slate-800/60 border border-slate-700/50 shadow-inner">
              <span className="text-xs text-slate-500 uppercase tracking-wider mr-2 font-semibold">Transport</span>
              <span className="text-sm font-semibold text-brand-400">{status.transport}</span>
            </div>
            <div className="flex items-center px-4 py-2.5 rounded-xl bg-slate-800/60 border border-slate-700/50 shadow-inner">
              <span className="text-xs text-slate-500 uppercase tracking-wider mr-2 font-semibold">Tools Loaded</span>
              <span className="text-sm font-semibold text-white">{status.tools_count}</span>
            </div>
          </div>
        )}
      </div>

      {/* Available Tools */}
      <div className="glass-panel p-6">
        <div className="flex items-center space-x-3 mb-6">
          <div className="p-2 rounded-xl bg-purple-500/20 border border-purple-500/30 text-purple-400 shadow-lg shadow-purple-500/10">
            <Wrench className="w-5 h-5" />
          </div>
          <h2 className="text-lg font-semibold text-white">Available tools</h2>
        </div>

        <div className="grid grid-cols-1 gap-5">
          {tools.map(tool => (
            <article key={tool.name} className="p-5 bg-slate-800/40 border border-slate-700/50 rounded-2xl transition-colors hover:bg-slate-800/60">
              <h3 className="font-mono text-sm font-bold text-brand-400 mb-2">{tool.name}</h3>
              <p className="text-sm text-slate-300 mb-4">{tool.description}</p>
              
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 overflow-x-auto custom-scrollbar shadow-inner">
                <pre className="text-xs font-mono text-slate-400 leading-relaxed">
                  {JSON.stringify(tool.input_schema, null, 2)}
                </pre>
              </div>
            </article>
          ))}
          {tools.length === 0 && !error && (
             <p className="text-slate-500 text-sm">No tools are currently registered.</p>
          )}
        </div>
      </div>

      {/* Recent Tool Calls */}
      <div className="glass-panel p-6">
        <div className="flex items-center space-x-3 mb-6">
          <div className="p-2 rounded-xl bg-orange-500/20 border border-orange-500/30 text-orange-400 shadow-lg shadow-orange-500/10">
            <Activity className="w-5 h-5" />
          </div>
          <h2 className="text-lg font-semibold text-white">Recent tool calls</h2>
        </div>

        {calls.length === 0 ? (
          <div className="text-center py-8">
            <Activity className="w-12 h-12 text-slate-700 mx-auto mb-4" />
            <p className="text-sm text-slate-500 max-w-md mx-auto leading-relaxed">
              No MCP tool calls yet. These tools are available to external MCP clients (like Claude Desktop) and are not automatically invoked by the LabTrace AI analysis pipeline.
            </p>
          </div>
        ) : (
          <ul className="space-y-3">
            {calls.map((call, i) => (
              <li key={i} className="flex items-center justify-between p-4 bg-slate-800/40 border border-slate-700/50 rounded-xl">
                <div className="flex items-center">
                  <Wrench className="w-4 h-4 text-slate-500 mr-3" />
                  <span className="font-mono text-sm text-slate-300">{call.name}</span>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                  call.status === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/20' :
                  call.status === 'FAILED' ? 'bg-red-500/20 text-red-400 border border-red-500/20' :
                  'bg-slate-700/50 text-slate-400 border border-slate-700/50'
                }`}>
                  {call.status}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};
