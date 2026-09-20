import React, { useEffect, useState } from 'react';
import { Cpu, Loader2 } from 'lucide-react';
import { experimentApi } from '../services/api';

export const McpPage: React.FC = () => {
  const [status, setStatus] = useState<any>(null); const [tools, setTools] = useState<any[]>([]); const [calls, setCalls] = useState<any[]>([]); const [error, setError] = useState<string | null>(null);
  useEffect(() => { Promise.all([experimentApi.getMcpStatus(), experimentApi.getMcpTools(), experimentApi.getMcpCalls()]).then(([s,t,c]) => { setStatus(s); setTools(t); setCalls(c); }).catch((err:any) => setError(err.response?.data?.detail || 'Unable to load MCP status')); }, []);
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">MCP Server Hub</h1>
        <p className="text-sm text-slate-500 mt-1">Model Context Protocol tools & connection status for Claude, Cursor, and Gemini.</p>
      </div>
      <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-4">
        <div className="flex items-center space-x-3 mb-4">
          <Cpu className="w-6 h-6 text-indigo-600" />
          <h3 className="font-semibold text-slate-800">MCP service status</h3>
        </div>
        {error ? <p className="text-sm text-red-600">{error}</p> : !status ? <Loader2 className="w-5 h-5 animate-spin text-slate-400" /> : <p className="text-sm text-slate-600">{status.status} · {status.transport} · {status.tools_count} tools</p>}
      </div>
      <div className="bg-white p-6 rounded-xl border border-slate-200"><h2 className="font-semibold text-slate-800">Available tools</h2><div className="mt-4 space-y-3">{tools.map(tool => <article key={tool.name} className="p-3 bg-slate-50 rounded-lg"><p className="font-mono text-sm font-semibold text-indigo-700">{tool.name}</p><p className="text-sm text-slate-600 mt-1">{tool.description}</p><pre className="mt-2 text-xs text-slate-500 overflow-auto">{JSON.stringify(tool.input_schema, null, 2)}</pre></article>)}</div></div>
      <div className="bg-white p-6 rounded-xl border border-slate-200"><h2 className="font-semibold text-slate-800">Recent tool calls</h2>{calls.length === 0 ? <p className="mt-3 text-sm text-slate-500">No MCP tool calls yet. These tools are available to MCP clients and are not automatically invoked by AI analysis.</p> : <ul className="mt-3 text-sm text-slate-600">{calls.map((call, i) => <li key={i}>{call.name} — {call.status}</li>)}</ul>}</div>
    </div>
  );
};
