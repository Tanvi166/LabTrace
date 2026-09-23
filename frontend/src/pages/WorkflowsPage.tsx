import React, { useEffect, useState } from 'react';
import { 
  Workflow, Loader2, AlertCircle, Check, Play, Clock,
  Network, Database, Code2, LineChart, ShieldCheck, Brain, FileOutput
} from 'lucide-react';
import { AgentRunDetail, experimentApi, AgentDetail } from '../services/api';

const pipeline = [
  'Coordinator Agent',
  'Metadata Agent',
  'Code Analysis Agent',
  'Results Agent',
  'Reproducibility Agent',
  'Knowledge Agent',
  'Report Agent'
];

const getAgentIcon = (name: string) => {
  switch (name) {
    case 'Coordinator Agent': return <Network className="w-5 h-5 text-indigo-400" />;
    case 'Metadata Agent': return <Database className="w-5 h-5 text-emerald-400" />;
    case 'Code Analysis Agent': return <Code2 className="w-5 h-5 text-brand-400" />;
    case 'Results Agent': return <LineChart className="w-5 h-5 text-orange-400" />;
    case 'Reproducibility Agent': return <ShieldCheck className="w-5 h-5 text-yellow-400" />;
    case 'Knowledge Agent': return <Brain className="w-5 h-5 text-purple-400" />;
    case 'Report Agent': return <FileOutput className="w-5 h-5 text-sky-400" />;
    default: return <Workflow className="w-5 h-5 text-slate-400" />;
  }
};

const getAgentColorBg = (name: string) => {
  switch (name) {
    case 'Coordinator Agent': return 'bg-indigo-500/20 border-indigo-500/30';
    case 'Metadata Agent': return 'bg-emerald-500/20 border-emerald-500/30';
    case 'Code Analysis Agent': return 'bg-brand-500/20 border-brand-500/30';
    case 'Results Agent': return 'bg-orange-500/20 border-orange-500/30';
    case 'Reproducibility Agent': return 'bg-yellow-500/20 border-yellow-500/30';
    case 'Knowledge Agent': return 'bg-purple-500/20 border-purple-500/30';
    case 'Report Agent': return 'bg-sky-500/20 border-sky-500/30';
    default: return 'bg-slate-500/20 border-slate-500/30';
  }
};

const formatTimeAgo = (dateStr: string | null) => {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins} min ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} hr ago`;
  return `${Math.floor(hours / 24)} days ago`;
};

export const WorkflowsPage: React.FC = () => {
  const [runs, setRuns] = useState<AgentRunDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      setError(null);
      const summaries = await experimentApi.getAgentRuns();
      const details = await Promise.all(summaries.map(async (run) => ({
        ...run,
        agents: await experimentApi.getAnalysisRunAgents(run.analysis_run_id),
      })));
      setRuns(details);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load workflow state.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const timer = window.setInterval(load, 3000);
    return () => window.clearInterval(timer);
  }, []);

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center text-slate-400">
        <Loader2 className="w-6 h-6 animate-spin mr-3 text-brand-500" />
        Loading AI Analysis Workflows...
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-8">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">AI Analysis in Progress</h1>
        <p className="text-sm text-slate-400">Track the execution of multi-agent analysis.</p>
      </div>

      {error && (
        <div className="p-4 bg-red-900/20 border border-red-500/30 text-red-400 rounded-xl text-sm flex items-center">
          <AlertCircle className="w-5 h-5 mr-3" />
          {error}
        </div>
      )}

      {runs.length === 0 ? (
        <div className="glass-panel p-12 text-center flex flex-col items-center justify-center">
          <Workflow className="w-16 h-16 text-slate-600 mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">No AI workflows yet</h3>
          <p className="text-slate-400">Run a comparison or analysis to trigger an agent workflow.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {runs.map((run) => {
            const isFinished = run.status === 'COMPLETED' || run.status === 'FAILED';
            const completedCount = run.completed_agents.length;
            const progressPercent = run.agent_count > 0 
              ? Math.round((completedCount / run.agent_count) * 100) 
              : 0;

            const timeAgoStr = formatTimeAgo(run.started_at);

            return (
              <section key={run.analysis_run_id} className="glass-panel p-6">
                
                {/* Run Header & Progress Bar */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                  <div className="flex items-center space-x-6 flex-1">
                    <h2 className="text-lg font-bold text-white tracking-wide">
                      {run.experiment_title || 'Unknown Experiment'}
                    </h2>
                    
                    <div className="flex items-center space-x-3 flex-1 max-w-sm">
                      <span className="text-sm font-semibold text-white min-w-[70px]">
                        {run.status === 'RUNNING' ? 'Running' : run.status === 'COMPLETED' ? 'Completed' : 'Failed'}
                      </span>
                      <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full transition-all duration-1000 ${
                            run.status === 'FAILED' ? 'bg-red-500' : 'bg-brand-400'
                          }`}
                          style={{ width: `${progressPercent}%` }}
                        />
                      </div>
                      <span className="text-xs font-semibold text-slate-400 min-w-[40px] text-right">
                        {progressPercent}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Timeline UI */}
                {run.agent_count === 0 && run.completed_agents.length === 0 && run.failed_agents.length === 0 ? (
                  <p className="text-sm text-slate-500 italic">No agent workflow recorded for this run.</p>
                ) : (
                  <div className="space-y-0 relative ml-2">
                    {pipeline.map((name, i) => {
                      const agent = run.agents.find(a => a.agent_name === name);
                      const status = agent?.status || (run.status === 'COMPLETED' ? 'COMPLETED' : 'PENDING');
                      
                      const isCompleted = status === 'COMPLETED';
                      const isRunning = status === 'RUNNING';
                      const isFailed = status === 'FAILED';
                      const isPending = status === 'PENDING';
                      
                      const isLast = i === pipeline.length - 1;
                      const nextAgent = !isLast ? run.agents.find(a => a.agent_name === pipeline[i + 1]) : null;
                      const nextStatus = nextAgent?.status || (run.status === 'COMPLETED' ? 'COMPLETED' : 'PENDING');
                      const lineCompleted = isCompleted && (nextStatus === 'COMPLETED' || nextStatus === 'RUNNING');

                      return (
                        <div key={name} className="relative flex items-start">
                          
                          {/* Connection Line */}
                          {!isLast && (
                            <div 
                              className={`absolute left-5 top-12 bottom-[-16px] w-0.5 rounded-full transition-colors duration-500 z-0 ${
                                lineCompleted ? 'bg-brand-500/80 shadow-[0_0_8px_rgba(6,182,212,0.5)]' : 'bg-slate-700/50'
                              }`}
                            />
                          )}

                          {/* Icon Square */}
                          <div className={`relative z-10 flex-shrink-0 w-10 h-10 rounded-xl border flex items-center justify-center mr-5 transition-colors ${
                            isCompleted || isRunning ? getAgentColorBg(name) : 'bg-slate-800/40 border-slate-700/40'
                          }`}>
                            {getAgentIcon(name)}
                          </div>

                          {/* Content Row */}
                          <div className="flex-1 pb-8 flex justify-between items-center pr-2">
                            <div>
                              <h4 className={`font-semibold text-sm mb-1 ${
                                isCompleted || isRunning ? 'text-slate-200' : 'text-slate-500'
                              }`}>
                                {name}
                              </h4>
                              <p className="text-xs text-slate-400">
                                {agent?.summary || (isPending ? 'Waiting for previous step...' : 'No summary provided.')}
                              </p>
                              {isFailed && agent?.error_message && (
                                <p className="text-xs text-red-400 mt-1 max-w-md line-clamp-2">
                                  {agent.error_message}
                                </p>
                              )}
                            </div>

                            <div className="flex items-center gap-4">
                              {/* Status Badge */}
                              <div className={`flex items-center px-3 py-1.5 rounded-lg border text-xs font-semibold whitespace-nowrap transition-colors ${
                                isCompleted ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
                                isRunning ? 'bg-brand-500/10 border-brand-500/20 text-brand-400' :
                                isFailed ? 'bg-red-500/10 border-red-500/20 text-red-400' :
                                'bg-slate-800/40 border-slate-700/40 text-slate-500'
                              }`}>
                                {isCompleted && <Check className="w-3.5 h-3.5 mr-1.5" />}
                                {isRunning && <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
                                {isFailed && <AlertCircle className="w-3.5 h-3.5 mr-1.5" />}
                                {isPending && <Clock className="w-3.5 h-3.5 mr-1.5" />}
                                {status.charAt(0) + status.slice(1).toLowerCase()}
                              </div>
                              
                              {/* Timestamp */}
                              <div className="w-20 text-right">
                                {(isCompleted || isRunning) && (
                                  <span className="text-xs text-slate-500 font-medium">{timeAgoStr}</span>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
};
