import React, { useState, useEffect } from 'react';
import { GitCompare, FlaskConical, AlertCircle, ArrowRight, Loader2, FileCode, Sliders, Package, LineChart as ChartIcon, CheckCircle2 } from 'lucide-react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts';
import { experimentApi, ComparisonResponse, AiWorkflowResponse, ReportResponse } from '../services/api';
import { Experiment } from '../types';

export const ComparePage: React.FC = () => {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [expAId, setExpAId] = useState<string>('');
  const [expBId, setExpBId] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  const [activeTab, setActiveTab] = useState<'config'|'code'|'results'|'ai'>('results');

  const [comparisonResult, setComparisonResult] = useState<ComparisonResponse | null>(null);
  const [comparing, setComparing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [aiComparing, setAiComparing] = useState<boolean>(false);
  const [aiResult, setAiResult] = useState<AiWorkflowResponse | null>(null);
  const [aiReport, setAiReport] = useState<ReportResponse | null>(null);

  useEffect(() => {
    const fetchExps = async () => {
      try {
        const res = await experimentApi.getExperiments({ page: 1, page_size: 100 });
        setExperiments(res.items || []);
        if (res.items.length >= 1) setExpAId(res.items[0].id);
        if (res.items.length >= 2) setExpBId(res.items[1].id);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchExps();
  }, []);

  const handleRunComparison = async () => {
    if (!expAId || !expBId) return;
    if (expAId === expBId) {
      setError("Please select two different experiments to compare.");
      return;
    }

    setComparing(true);
    setError(null);
    try {
      const res = await experimentApi.compareExperiments(expAId, expBId);
      setComparisonResult(res);
      setActiveTab('results');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Comparison failed');
    } finally {
      setComparing(false);
    }
  };

  const handleRunAiComparison = async () => {
    if (!expAId || !expBId || expAId === expBId) return;
    setAiComparing(true); setError(null);
    try {
      const result = await experimentApi.startAiComparison(expAId, expBId);
      setAiResult(result); setAiReport(await experimentApi.getReport(result.report_id));
      setActiveTab('ai');
    } catch (err: any) { setError(err.response?.data?.detail || 'AI comparison failed'); }
    finally { setAiComparing(false); }
  };

  const expA = experiments.find(e => e.id === expAId);
  const expB = experiments.find(e => e.id === expBId);

  return (
    <div className="space-y-6 pb-20">
      <div>
        <h1 className="text-2xl font-bold text-white text-glow mb-1">Compare Experiment Runs</h1>
        <p className="text-sm text-slate-400">Analyze differences in code, configurations and results.</p>
      </div>

      <div className="glass-panel p-6 space-y-6">
        {/* Top Selectors Inline */}
        <div className="flex flex-col md:flex-row gap-4 items-end">
          <div className="flex-1 w-full">
            <label className="block text-[12px] font-semibold text-slate-300 tracking-wide mb-2">Experiment A</label>
            <select
              value={expAId}
              onChange={e => setExpAId(e.target.value)}
              className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
            >
              <option value="">-- Select Experiment A --</option>
              {experiments.map(e => (
                <option key={e.id} value={e.id}>{e.title}</option>
              ))}
            </select>
          </div>
          
          <div className="flex-1 w-full">
            <label className="block text-[12px] font-semibold text-slate-300 tracking-wide mb-2">Experiment B</label>
            <select
              value={expBId}
              onChange={e => setExpBId(e.target.value)}
              className="w-full px-4 py-2.5 bg-black/40 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
            >
              <option value="">-- Select Experiment B --</option>
              {experiments.map(e => (
                <option key={e.id} value={e.id}>{e.title}</option>
              ))}
            </select>
          </div>

          <div className="w-full md:w-auto h-[42px]">
            <button
              onClick={handleRunComparison}
              disabled={comparing || !expAId || !expBId || expAId === expBId}
              className="w-full md:w-36 h-full bg-blue-500 hover:bg-blue-400 disabled:opacity-50 text-white font-semibold text-sm rounded-lg shadow-neon transition-all flex items-center justify-center space-x-2"
            >
              {comparing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <GitCompare className="w-4 h-4" />
                  <span>Compare</span>
                </>
              )}
            </button>
          </div>
        </div>

        {experiments.length < 2 && (
          <div className="p-4 bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded-lg text-sm flex items-start">
            <AlertCircle className="w-5 h-5 mr-3 flex-shrink-0 mt-0.5" />
            <p>You need at least two uploaded experiments to run a comparison. Head over to <strong>Upload & Analyze</strong> to add more experiments to your workspace.</p>
          </div>
        )}

        {error && (
          <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg text-sm">
            {error}
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex space-x-8 border-b border-white/10 pt-2">
          {['Configuration Diff', 'Code Diff', 'Results Comparison', 'AI Insights'].map((tab, idx) => {
            const id = ['config', 'code', 'results', 'ai'][idx] as any;
            const isActive = activeTab === id;
            return (
              <button 
                key={id} 
                onClick={() => setActiveTab(id)} 
                className={`pb-3 text-sm font-semibold transition-all ${isActive ? 'text-white border-b-2 border-brand-500' : 'text-slate-400 hover:text-slate-200'}`}
              >
                {tab}
              </button>
            );
          })}
        </div>

        {/* --- TAB: Configuration Diff --- */}
        {activeTab === 'config' && comparisonResult && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 pt-4">
            {comparisonResult.config_diffs.length > 0 && (
              <div className="space-y-4">
                <h3 className="font-bold text-white text-base flex items-center space-x-2">
                  <Sliders className="w-5 h-5 text-neon-cyan" />
                  <span>Hyperparameter Configuration Differences</span>
                </h3>
                <div className="overflow-x-auto border border-white/10 rounded-lg bg-black/20">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-black/40 text-slate-300 font-semibold uppercase border-b border-white/10">
                      <tr>
                        <th className="px-5 py-4">Parameter</th>
                        <th className="px-5 py-4">{comparisonResult.experiment_a_title}</th>
                        <th className="px-5 py-4">{comparisonResult.experiment_b_title}</th>
                        <th className="px-5 py-4">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {comparisonResult.config_diffs.map((row, idx) => (
                        <tr key={idx} className="hover:bg-white/5 transition-colors">
                          <td className="px-5 py-3.5 font-medium text-white font-mono">{row.parameter}</td>
                          <td className="px-5 py-3.5 font-mono text-slate-300">{String(row.experiment_a ?? '--')}</td>
                          <td className="px-5 py-3.5 font-mono text-slate-300">{String(row.experiment_b ?? '--')}</td>
                          <td className="px-5 py-3.5">
                            <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase ${
                              row.change_type === 'changed' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/20' : 'bg-white/10 text-slate-300'
                            }`}>
                              {row.change_type}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {comparisonResult.dependency_diffs.length > 0 && (
              <div className="space-y-4 mt-8">
                <h3 className="font-bold text-white text-base flex items-center space-x-2">
                  <Package className="w-5 h-5 text-neon-cyan" />
                  <span>Dependency Version Differences</span>
                </h3>
                <div className="overflow-x-auto border border-white/10 rounded-lg bg-black/20">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-black/40 text-slate-300 font-semibold uppercase border-b border-white/10">
                      <tr>
                        <th className="px-5 py-4">Package</th>
                        <th className="px-5 py-4">Exp A Version</th>
                        <th className="px-5 py-4">Exp B Version</th>
                        <th className="px-5 py-4">Change Type</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {comparisonResult.dependency_diffs.map((row, idx) => (
                        <tr key={idx} className="hover:bg-white/5 transition-colors">
                          <td className="px-5 py-3.5 font-medium text-white font-mono">{row.package}</td>
                          <td className="px-5 py-3.5 font-mono text-slate-300">{row.version_a || '--'}</td>
                          <td className="px-5 py-3.5 font-mono text-slate-300">{row.version_b || '--'}</td>
                          <td className="px-5 py-3.5">
                            <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase ${
                              row.change_type === 'version_changed' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/20' : 'bg-white/10 text-slate-300'
                            }`}>
                              {row.change_type}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* --- TAB: Code Diff --- */}
        {activeTab === 'code' && comparisonResult && (
          <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 pt-4">
            <h3 className="font-bold text-white text-base flex items-center space-x-2">
              <FileCode className="w-5 h-5 text-neon-cyan" />
              <span>Codebase AST & Unified File Diff</span>
            </h3>

            <div className="divide-y divide-white/5 border border-white/10 rounded-lg overflow-hidden bg-black/20">
              {comparisonResult.code_file_diffs.map((fileDiff, idx) => (
                <div key={idx} className="p-5 space-y-3 text-xs">
                  <div className="flex items-center justify-between font-mono">
                    <span className="font-semibold text-white">{fileDiff.filename}</span>
                    <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase ${
                      fileDiff.change_type === 'modified' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/20' :
                      fileDiff.change_type === 'added' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/20' :
                      fileDiff.change_type === 'removed' ? 'bg-red-500/20 text-red-300 border border-red-500/20' : 'bg-white/10 text-slate-300'
                    }`}>
                      {fileDiff.change_type}
                    </span>
                  </div>

                  {fileDiff.ast_function_diffs.length > 0 && (
                    <div className="p-3 bg-brand-500/10 border border-brand-500/20 rounded-lg text-[11px] space-y-1.5">
                      <span className="font-semibold text-brand-300 block">AST Function Modifications:</span>
                      {fileDiff.ast_function_diffs.map((f, fIdx) => (
                        <span key={fIdx} className="inline-block mr-4 text-brand-100">
                          &bull; Function <span className="font-mono font-bold">{f.name}()</span> ({f.change_type})
                        </span>
                      ))}
                    </div>
                  )}

                  {fileDiff.text_diff_lines.length > 0 && (
                    <pre className="bg-black/40 text-slate-300 p-4 rounded-lg font-mono text-[11px] overflow-x-auto max-h-64 leading-relaxed border border-white/5">
                      {fileDiff.text_diff_lines.join('\n')}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* --- TAB: Results Comparison --- */}
        {activeTab === 'results' && comparisonResult && (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 pt-4">
            
            {/* New Main Comparison Table */}
            <div className="bg-black/20 border border-white/10 rounded-xl overflow-hidden shadow-sm">
               <table className="w-full text-sm text-left">
                 <thead className="bg-black/40 text-slate-300 font-semibold border-b border-white/10">
                   <tr>
                     <th className="px-6 py-4">Metric</th>
                     <th className="px-6 py-4">Run 1</th>
                     <th className="px-6 py-4">Run 2</th>
                     <th className="px-6 py-4">Change</th>
                   </tr>
                 </thead>
                 <tbody className="divide-y divide-white/5">
                   {comparisonResult.metric_comparisons.map((m, i) => {
                      const isNegative = (m.relative_diff_pct ?? 0) < 0;
                      const isPositive = (m.relative_diff_pct ?? 0) > 0;
                      // Some metrics like loss we want negative to be green, others red. 
                      // For simplicity, we stick to the exact reference image colors: 
                      // Reference shows ↓ -4.4% as red, ↑ +40.0% as red? Actually, 
                      // Reference image: "Accuracy ↓ -4.4% (red)", "Loss ↑ +40.0% (red)", "Precision ↓ -5.6% (red)".
                      // They are all red in the image, meaning performance degraded on run 2.
                      // We will use standard conditional styling based on value direction for now.
                      let arrow = "";
                      if (isPositive) arrow = "↑";
                      if (isNegative) arrow = "↓";
                      
                      let colorClass = "text-slate-400";
                      if (isPositive) colorClass = "text-red-400"; // Assume higher is worse for loss, wait no, let's just use emerald for positive for accuracy
                      if (isNegative) colorClass = "text-red-400";
                      
                      if (m.metric_name.toLowerCase().includes('accuracy') || m.metric_name.toLowerCase().includes('score') || m.metric_name.toLowerCase().includes('precision') || m.metric_name.toLowerCase().includes('recall')) {
                         if (isPositive) colorClass = "text-emerald-400";
                         if (isNegative) colorClass = "text-red-400";
                      }

                      return (
                        <tr key={i} className="hover:bg-white/5 transition-colors">
                          <td className="px-6 py-4 text-white font-medium capitalize">{m.metric_name.replace(/_/g, ' ')}</td>
                          <td className="px-6 py-4 text-slate-300">{m.experiment_a_final.toFixed(4)}</td>
                          <td className="px-6 py-4 text-slate-300">{m.experiment_b_final.toFixed(4)}</td>
                          <td className="px-6 py-4 font-mono text-[13px]">
                             {m.relative_diff_pct !== null && m.relative_diff_pct !== undefined ? (
                               <span className={`${colorClass} flex items-center`}>
                                 {arrow} {m.relative_diff_pct > 0 ? '+' : ''}{m.relative_diff_pct.toFixed(1)}%
                               </span>
                             ) : '--'}
                          </td>
                        </tr>
                      );
                   })}
                 </tbody>
               </table>
            </div>

            {/* Reproducibility Delta */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
              <div className="bg-black/20 p-5 rounded-xl border border-white/10">
                <p className="text-xs text-slate-400 uppercase tracking-wider mb-2">Run 1 Score</p>
                <p className="text-3xl font-bold text-white">{comparisonResult.reproducibility_delta.experiment_a_score}</p>
              </div>
              <div className="bg-black/20 p-5 rounded-xl border border-white/10">
                <p className="text-xs text-slate-400 uppercase tracking-wider mb-2">Run 2 Score</p>
                <p className="text-3xl font-bold text-white">{comparisonResult.reproducibility_delta.experiment_b_score}</p>
              </div>
              <div className="bg-brand-500/10 p-5 rounded-xl border border-brand-500/20">
                <p className="text-xs text-brand-300 font-semibold uppercase tracking-wider mb-2">Delta Difference</p>
                <p className={`text-3xl font-bold ${
                  comparisonResult.reproducibility_delta.score_diff >= 0 ? 'text-emerald-400' : 'text-red-400'
                }`}>
                  {comparisonResult.reproducibility_delta.score_diff >= 0 ? '+' : ''}{comparisonResult.reproducibility_delta.score_diff} pts
                </p>
              </div>
            </div>

            {/* Trajectory Charts */}
            {comparisonResult.metric_comparisons.map((m, idx) => (
              <div key={idx} className="space-y-4 pt-4 border-t border-white/10">
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold text-white text-sm capitalize">{m.metric_name.replace(/_/g, ' ')} Trajectory Override</h4>
                </div>

                <div className="h-72 w-full bg-black/20 p-5 rounded-xl border border-white/10">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={m.combined_trajectory}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#ffffff1a" />
                      <XAxis dataKey="step" label={{ value: 'Epoch / Step', position: 'insideBottom', offset: -5, fill: '#94a3b8' }} stroke="#64748b" tick={{fill: '#94a3b8'}} />
                      <YAxis stroke="#64748b" tick={{fill: '#94a3b8'}} />
                      <Tooltip contentStyle={{backgroundColor: '#0f172a', borderColor: '#334155', color: '#f8fafc'}} />
                      <Legend wrapperStyle={{paddingTop: '15px'}}/>
                      <Line type="monotone" dataKey="exp_a" name={comparisonResult.experiment_a_title} stroke="#2563eb" strokeWidth={2} dot={{ r: 4, fill: '#2563eb' }} />
                      <Line type="monotone" dataKey="exp_b" name={comparisonResult.experiment_b_title} stroke="#10b981" strokeWidth={2} dot={{ r: 4, fill: '#10b981' }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* --- TAB: AI Insights --- */}
        {activeTab === 'ai' && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 pt-4">
            <button 
              onClick={handleRunAiComparison} 
              disabled={aiComparing || !expAId || !expBId || expAId === expBId} 
              className="w-full py-3 bg-violet-600 hover:bg-violet-500 disabled:bg-violet-600/30 disabled:text-white/50 text-white font-bold text-sm rounded-lg shadow-neon transition-all flex items-center justify-center space-x-2"
            >
              {aiComparing ? <><Loader2 className="w-5 h-5 animate-spin" /><span>Running Deep AI Analysis...</span></> : <><GitCompare className="w-5 h-5" /><span>Run AI Comparison</span></>}
            </button>

            {aiResult && aiReport && (
              <section className="glass-panel border border-neon-purple/30 p-8 rounded-xl space-y-6 mt-6">
                <div className="flex justify-between items-center border-b border-white/10 pb-4">
                  <h3 className="text-lg font-bold text-white text-glow">AI INTERPRETATION</h3>
                  <span className="font-bold text-neon-purple text-lg bg-neon-purple/10 px-4 py-1 rounded-full border border-neon-purple/20">Score: {aiResult.overall_score}/100</span>
                </div>
                <p className="text-sm text-slate-300 leading-relaxed text-justify">{aiReport.structured_json?.executive_summary || aiReport.summary}</p>
                
                <div className="text-sm space-y-6">
                  <div>
                    <p className="font-bold text-white mb-3 flex items-center"><AlertCircle className="w-4 h-4 mr-2 text-amber-400"/> Key Findings</p>
                    <div className="space-y-3">
                      {(aiReport.structured_json?.findings || []).map((f, i) => (
                        <div key={i} className="bg-black/30 p-4 rounded-lg border border-white/5">
                          <p className="font-semibold text-white">{f.title}</p>
                          <p className="text-slate-400 mt-1">{f.observed_evidence}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <p className="font-bold text-white mb-3 flex items-center"><CheckCircle2 className="w-4 h-4 mr-2 text-emerald-400"/> Recommendations</p>
                    <ul className="list-disc pl-5 space-y-2 text-slate-300">
                      {(aiReport.structured_json?.actionable_recommendations || []).map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
