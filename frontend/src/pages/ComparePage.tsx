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
    } catch (err: any) { setError(err.response?.data?.detail || 'AI comparison failed'); }
    finally { setAiComparing(false); }
  };

  const expA = experiments.find(e => e.id === expAId);
  const expB = experiments.find(e => e.id === expBId);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Compare Experiments</h1>
        <p className="text-sm text-slate-500 mt-1">Side-by-side AST code diffs, hyperparameter delta tables, and metric trajectory overlays.</p>
      </div>

      {/* Selectors */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">Experiment A (Base)</label>
            <select
              value={expAId}
              onChange={e => setExpAId(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">-- Select Experiment A --</option>
              {experiments.map(e => (
                <option key={e.id} value={e.id}>{e.title}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">Experiment B (Variant)</label>
            <select
              value={expBId}
              onChange={e => setExpBId(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">-- Select Experiment B --</option>
              {experiments.map(e => (
                <option key={e.id} value={e.id}>{e.title}</option>
              ))}
            </select>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-red-50 text-red-700 rounded-lg text-xs">
            {error}
          </div>
        )}

        <button
          onClick={handleRunComparison}
          disabled={comparing || !expAId || !expBId || expAId === expBId}
          className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-semibold text-sm rounded-lg shadow-sm transition-colors flex items-center justify-center space-x-2"
        >
          {comparing ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Comparing Codebases & Metrics...</span>
            </>
          ) : (
            <>
              <GitCompare className="w-4 h-4" />
              <span>Compare Experiments</span>
            </>
          )}
        </button>
        <button onClick={handleRunAiComparison} disabled={aiComparing || !expAId || !expBId || expAId === expBId} className="w-full py-2.5 bg-violet-600 hover:bg-violet-700 disabled:bg-violet-400 text-white font-semibold text-sm rounded-lg shadow-sm transition-colors flex items-center justify-center space-x-2">
          {aiComparing ? <><Loader2 className="w-4 h-4 animate-spin" /><span>Running AI Comparison...</span></> : <><GitCompare className="w-4 h-4" /><span>Run AI Comparison</span></>}
        </button>
      </div>

      {comparisonResult && <p className="text-xs font-bold tracking-wider text-slate-500">DETERMINISTIC EVIDENCE</p>}

      {aiResult && aiReport && <section className="bg-violet-50 border border-violet-200 p-6 rounded-xl space-y-3"><div className="flex justify-between"><h3 className="font-bold text-violet-950">AI INTERPRETATION</h3><span className="font-bold text-violet-800">Score: {aiResult.overall_score}/100</span></div><p className="text-sm text-violet-900">{aiReport.structured_json?.executive_summary || aiReport.summary}</p><div className="text-sm text-violet-900"><p className="font-semibold">Findings</p><ul className="list-disc pl-5">{(aiReport.structured_json?.findings || []).map((f, i) => <li key={i}>{f.title}: {f.observed_evidence}</li>)}</ul><p className="font-semibold mt-2">Recommendations</p><ul className="list-disc pl-5">{(aiReport.structured_json?.actionable_recommendations || []).map((r, i) => <li key={i}>{r}</li>)}</ul></div></section>}

      {/* Comparison Results Section */}
      {comparisonResult && (
        <div className="space-y-6">
          {/* Reproducibility Delta Card */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-900 text-base flex items-center space-x-2">
              <GitCompare className="w-5 h-5 text-indigo-600" />
              <span>Reproducibility Score Delta</span>
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
              <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                <p className="text-xs text-slate-500">Experiment A Score</p>
                <p className="text-2xl font-bold text-slate-800">{comparisonResult.reproducibility_delta.experiment_a_score}</p>
              </div>
              <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                <p className="text-xs text-slate-500">Experiment B Score</p>
                <p className="text-2xl font-bold text-slate-800">{comparisonResult.reproducibility_delta.experiment_b_score}</p>
              </div>
              <div className="bg-indigo-50 p-4 rounded-lg border border-indigo-200">
                <p className="text-xs text-indigo-600 font-semibold">Delta Difference</p>
                <p className={`text-2xl font-bold ${
                  comparisonResult.reproducibility_delta.score_diff >= 0 ? 'text-emerald-700' : 'text-red-600'
                }`}>
                  {comparisonResult.reproducibility_delta.score_diff >= 0 ? '+' : ''}{comparisonResult.reproducibility_delta.score_diff} pts
                </p>
              </div>
            </div>
          </div>

          {/* Hyperparameter Config Differences */}
          {comparisonResult.config_diffs.length > 0 && (
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
              <h3 className="font-bold text-slate-900 text-base flex items-center space-x-2">
                <Sliders className="w-5 h-5 text-indigo-600" />
                <span>Hyperparameter Configuration Differences</span>
              </h3>
              <div className="overflow-x-auto border border-slate-200 rounded-lg">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 text-slate-500 font-semibold uppercase border-b border-slate-200">
                    <tr>
                      <th className="px-4 py-3">Parameter</th>
                      <th className="px-4 py-3">{comparisonResult.experiment_a_title}</th>
                      <th className="px-4 py-3">{comparisonResult.experiment_b_title}</th>
                      <th className="px-4 py-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {comparisonResult.config_diffs.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-50">
                        <td className="px-4 py-2.5 font-medium text-slate-800 font-mono">{row.parameter}</td>
                        <td className="px-4 py-2.5 font-mono text-slate-600">{String(row.experiment_a ?? '--')}</td>
                        <td className="px-4 py-2.5 font-mono text-slate-600">{String(row.experiment_b ?? '--')}</td>
                        <td className="px-4 py-2.5">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            row.change_type === 'changed' ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-600'
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

          {/* Dependency Differences */}
          {comparisonResult.dependency_diffs.length > 0 && (
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
              <h3 className="font-bold text-slate-900 text-base flex items-center space-x-2">
                <Package className="w-5 h-5 text-indigo-600" />
                <span>Dependency Version Differences</span>
              </h3>
              <div className="overflow-x-auto border border-slate-200 rounded-lg">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 text-slate-500 font-semibold uppercase border-b border-slate-200">
                    <tr>
                      <th className="px-4 py-3">Package</th>
                      <th className="px-4 py-3">Exp A Version</th>
                      <th className="px-4 py-3">Exp B Version</th>
                      <th className="px-4 py-3">Change Type</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {comparisonResult.dependency_diffs.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-50">
                        <td className="px-4 py-2.5 font-medium text-slate-800 font-mono">{row.package}</td>
                        <td className="px-4 py-2.5 font-mono text-slate-600">{row.version_a || '--'}</td>
                        <td className="px-4 py-2.5 font-mono text-slate-600">{row.version_b || '--'}</td>
                        <td className="px-4 py-2.5">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            row.change_type === 'version_changed' ? 'bg-purple-100 text-purple-800' : 'bg-slate-100 text-slate-600'
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

          {/* Metric Trajectory Recharts Comparison */}
          {comparisonResult.metric_comparisons.length > 0 && (
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
              <h3 className="font-bold text-slate-900 text-base flex items-center space-x-2">
                <ChartIcon className="w-5 h-5 text-indigo-600" />
                <span>Metric Trajectory Overlay</span>
              </h3>
              {comparisonResult.metric_comparisons.map((m, idx) => (
                <div key={idx} className="space-y-3 pt-2">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-slate-800 text-sm capitalize">{m.metric_name} Curve Comparison</h4>
                    <span className="text-xs text-slate-500 font-mono">
                      Delta: {m.absolute_diff.toFixed(4)} ({m.relative_diff_pct !== null ? `${m.relative_diff_pct?.toFixed(1)}%` : '--'})
                    </span>
                  </div>

                  <div className="h-64 w-full bg-slate-50 p-4 rounded-lg border border-slate-200">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={m.combined_trajectory}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis dataKey="step" label={{ value: 'Epoch / Step', position: 'insideBottom', offset: -5 }} />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="exp_a" name={comparisonResult.experiment_a_title} stroke="#2563eb" strokeWidth={2} dot={{ r: 4 }} />
                        <Line type="monotone" dataKey="exp_b" name={comparisonResult.experiment_b_title} stroke="#16a34a" strokeWidth={2} dot={{ r: 4 }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Codebase & AST Differences */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-900 text-base flex items-center space-x-2">
              <FileCode className="w-5 h-5 text-indigo-600" />
              <span>Codebase AST & Unified File Diff</span>
            </h3>

            <div className="divide-y divide-slate-100 border border-slate-200 rounded-lg overflow-hidden">
              {comparisonResult.code_file_diffs.map((fileDiff, idx) => (
                <div key={idx} className="p-4 space-y-2 text-xs">
                  <div className="flex items-center justify-between font-mono">
                    <span className="font-semibold text-slate-800">{fileDiff.filename}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      fileDiff.change_type === 'modified' ? 'bg-amber-100 text-amber-800' :
                      fileDiff.change_type === 'added' ? 'bg-emerald-100 text-emerald-800' :
                      fileDiff.change_type === 'removed' ? 'bg-red-100 text-red-800' : 'bg-slate-100 text-slate-600'
                    }`}>
                      {fileDiff.change_type}
                    </span>
                  </div>

                  {fileDiff.ast_function_diffs.length > 0 && (
                    <div className="p-2 bg-indigo-50 border border-indigo-100 rounded text-[11px] space-y-1">
                      <span className="font-semibold text-indigo-900 block">AST Function Modifications:</span>
                      {fileDiff.ast_function_diffs.map((f, fIdx) => (
                        <span key={fIdx} className="inline-block mr-3 text-indigo-700">
                          &bull; Function <span className="font-mono font-bold">{f.name}()</span> ({f.change_type})
                        </span>
                      ))}
                    </div>
                  )}

                  {fileDiff.text_diff_lines.length > 0 && (
                    <pre className="bg-slate-900 text-slate-200 p-3 rounded font-mono text-[11px] overflow-x-auto max-h-48 leading-relaxed">
                      {fileDiff.text_diff_lines.join('\n')}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
