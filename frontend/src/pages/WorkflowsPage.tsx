import React, { useEffect, useState } from 'react';
import { Workflow, Loader2, AlertCircle } from 'lucide-react';
import { AgentRunDetail, experimentApi } from '../services/api';

const pipeline = ['Coordinator Agent', 'Metadata Agent', 'Code Analysis Agent', 'Results Agent', 'Reproducibility Agent', 'Knowledge Agent', 'Report Agent'];
const color = (status: string) => status === 'COMPLETED' ? 'bg-emerald-100 text-emerald-800' : status === 'FAILED' ? 'bg-red-100 text-red-800' : status === 'RUNNING' ? 'bg-blue-100 text-blue-800' : 'bg-slate-100 text-slate-600';

export const WorkflowsPage: React.FC = () => {
  const [runs, setRuns] = useState<AgentRunDetail[]>([]); const [loading, setLoading] = useState(true); const [error, setError] = useState<string | null>(null);
  const load = async () => {
    try {
      setError(null);
      const summaries = await experimentApi.getAgentRuns();
      const details = await Promise.all(summaries.map(async (run) => ({
        ...run,
        agents: await experimentApi.getAnalysisRunAgents(run.analysis_run_id),
      })));
      setRuns(details);
    } catch (err: any) { setError(err.response?.data?.detail || 'Failed to load workflow state.'); } finally { setLoading(false); }
  };
  useEffect(() => { load(); const timer = window.setInterval(load, 3000); return () => window.clearInterval(timer); }, []);
  if (loading) return <div className="p-12 text-center text-slate-500"><Loader2 className="w-5 h-5 animate-spin inline mr-2" />Loading workflows…</div>;
  return <div className="space-y-6"><div><h1 className="text-2xl font-bold text-slate-900">Multi-Agent Workflow Tracker</h1><p className="text-sm text-slate-500 mt-1">Live state from persisted analysis runs and agent logs.</p></div>{error && <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm"><AlertCircle className="w-4 h-4 inline mr-2" />{error}</div>}{runs.length === 0 ? <div className="bg-white p-8 rounded-xl border border-slate-200 text-center"><Workflow className="w-12 h-12 text-slate-400 mx-auto mb-3" /><h3 className="text-lg font-semibold text-slate-800">No AI workflows yet</h3></div> : runs.map(run => <section key={run.analysis_run_id} className="bg-white p-6 rounded-xl border border-slate-200"><div className="flex justify-between gap-4"><div><h2 className="font-bold text-slate-900">{run.experiment_title}</h2><p className="text-xs text-slate-500">Run {run.analysis_run_id} · {run.started_at && new Date(run.started_at).toLocaleString()}</p></div><span className={`h-fit px-2 py-1 rounded text-xs font-bold ${color(run.status)}`}>{run.status}</span></div><div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3 text-sm"><p><span className="text-slate-500">Score:</span> {run.overall_score ?? '—'}</p><p><span className="text-slate-500">Duration:</span> {run.duration_seconds != null ? `${run.duration_seconds}s` : '—'}</p><p><span className="text-slate-500">Agents:</span> {run.agent_count}</p><p><span className="text-slate-500">Failed:</span> {run.failed_agents.length}</p></div><p className="mt-3 text-xs text-slate-500">Completed: {run.completed_agents.join(', ') || 'None'}{run.failed_agents.length > 0 && ` · Failed: ${run.failed_agents.join(', ')}`}</p>{run.agent_count === 0 && run.completed_agents.length === 0 && run.failed_agents.length === 0 ? <p className="mt-5 text-sm text-slate-500">No agent workflow recorded for this run.</p> : <div className="mt-5 flex flex-col md:flex-row md:items-stretch gap-2">{pipeline.map((name, i) => { const agent = run.agents.find(a => a.agent_name === name); const status = agent?.status || 'PENDING'; return <React.Fragment key={name}><div className="flex-1 p-3 border rounded-lg"><p className="text-sm font-semibold text-slate-800">{name}</p><span className={`inline-block mt-2 px-2 py-0.5 rounded text-[11px] font-bold ${color(status)}`}>{status}</span>{agent?.summary && <p className="text-xs text-slate-500 mt-2">{agent.summary}</p>}{agent?.error_message && <p className="text-xs text-red-600 mt-2">{agent.error_message}</p>}</div>{i < pipeline.length - 1 && <div className="self-center text-slate-400 text-xl">↓</div>}</React.Fragment>; })}</div>}</section>)}</div>;
};
