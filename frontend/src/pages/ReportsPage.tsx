import React, { useEffect, useState } from 'react';
import { FileText, Loader2, AlertCircle, Award } from 'lucide-react';
import { experimentApi, ReportResponse } from '../services/api';

const sections: Array<[string, keyof NonNullable<ReportResponse['structured_json']>]> = [['Experiment overview', 'experiment_overview'], ['Environment analysis', 'environment_analysis'], ['Code & configuration', 'code_and_config_differences'], ['Results & metrics', 'results_and_metric_analysis'], ['Reproducibility assessment', 'reproducibility_assessment']];

export const ReportsPage: React.FC = () => {
  const [reports, setReports] = useState<ReportResponse[]>([]); const [selected, setSelected] = useState<ReportResponse | null>(null); const [loading, setLoading] = useState(true); const [error, setError] = useState<string | null>(null);
  useEffect(() => { const load = async () => { try { const list = await experimentApi.getReports(); setReports(list); if (list[0]) setSelected(await experimentApi.getReport(list[0].id)); } catch (err: any) { setError(err.response?.data?.detail || 'Failed to load reports.'); } finally { setLoading(false); } }; load(); }, []);
  const selectReport = async (report: ReportResponse) => { try { setSelected(await experimentApi.getReport(report.id)); } catch (err: any) { setError(err.response?.data?.detail || 'Failed to load report.'); } };
  if (loading) return <div className="p-12 text-center text-slate-500"><Loader2 className="w-5 h-5 animate-spin inline mr-2" />Loading reports…</div>;
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white text-glow">Reproducibility Reports</h1>
        <p className="text-sm text-slate-400 mt-1">Persisted reports generated from deterministic evidence and agent interpretation.</p>
      </div>
      {error && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg text-sm">
          <AlertCircle className="w-4 h-4 inline mr-2" />{error}
        </div>
      )}
      {reports.length === 0 ? (
        <div className="glass-panel p-8 text-center">
          <FileText className="w-12 h-12 text-slate-400 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-white">No Reports Generated Yet</h3>
          <p className="text-sm text-slate-400 mt-1">Run AI Analysis from an experiment to create a report.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <aside className="glass-panel divide-y divide-white/5 h-fit">
            {reports.map(report => (
              <button 
                key={report.id} 
                onClick={() => selectReport(report)} 
                className={`w-full text-left p-4 hover:bg-white/5 transition-colors ${selected?.id === report.id ? 'bg-brand-500/20 border-l-2 border-brand-500' : ''}`}
              >
                <p className="font-semibold text-sm text-white">{report.experiment_title || report.title}</p>
                <p className="text-xs text-slate-400 mt-1">Run {report.analysis_run_id.slice(0, 8)} · {new Date(report.created_at).toLocaleString()}</p>
                {report.overall_score != null && <span className="inline-block mt-2 text-xs font-bold text-neon-cyan">Score: {report.overall_score}/100</span>}
              </button>
            ))}
          </aside>
          {selected && (
            <article className="lg:col-span-2 glass-panel p-6 space-y-6">
              <div className="flex justify-between gap-4">
                <div>
                  <h2 className="text-xl font-bold text-white">{selected.title}</h2>
                  <p className="text-sm text-slate-400 mt-1">Experiment: {selected.experiment_title || selected.experiment_id} · Analysis run: {selected.analysis_run_id}</p>
                </div>
                {selected.structured_json?.overall_score != null && (
                  <div className="text-right">
                    <Award className="w-5 h-5 text-neon-cyan inline mr-1" />
                    <p className="font-bold text-lg text-white">{selected.structured_json.overall_score}/100</p>
                  </div>
                )}
              </div>
              <section>
                <h3 className="font-semibold text-white">Executive summary</h3>
                <p className="text-sm text-slate-300 mt-2 whitespace-pre-wrap">{selected.structured_json?.executive_summary || selected.summary}</p>
              </section>
              <section>
                <h3 className="font-semibold text-white">Findings</h3>
                <div className="mt-2 space-y-2">
                  {(selected.structured_json?.findings || []).map((finding, i) => (
                    <div key={i} className="p-3 bg-black/20 rounded-lg text-sm border border-white/5">
                      <p className="font-medium text-slate-200">{finding.title} <span className="text-xs text-slate-400 ml-2">{finding.severity}</span></p>
                      <p className="text-slate-400 mt-1">{finding.observed_evidence}</p>
                      <p className="text-brand-300 mt-1">Recommendation: {finding.recommendation}</p>
                    </div>
                  ))}
                </div>
              </section>
              <section>
                <h3 className="font-semibold text-white">Recommendations</h3>
                <ul className="mt-2 list-disc pl-5 text-sm text-slate-300">
                  {(selected.structured_json?.actionable_recommendations || []).map((item, i) => <li key={i}>{item}</li>)}
                </ul>
              </section>
              <section>
                <h3 className="font-semibold text-white">Report sections</h3>
                <div className="mt-2 space-y-3">
                  {sections.map(([label, key]) => selected.structured_json?.[key] && (
                    <div key={key}>
                      <p className="text-sm font-medium text-neon-cyan">{label}</p>
                      <p className="text-sm text-slate-300">{String(selected.structured_json[key])}</p>
                    </div>
                  ))}
                </div>
              </section>
            </article>
          )}
        </div>
      )}
    </div>
  );
};
