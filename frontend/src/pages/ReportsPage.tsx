import React, { useEffect, useState } from 'react';
import { FileText, Loader2, AlertCircle, X, Download, Eye, Plus } from 'lucide-react';
import { experimentApi, ReportResponse } from '../services/api';

const sections: Array<[string, keyof NonNullable<ReportResponse['structured_json']>]> = [
  ['Experiment overview', 'experiment_overview'], 
  ['Environment analysis', 'environment_analysis'], 
  ['Code & configuration', 'code_and_config_differences'], 
  ['Results & metrics', 'results_and_metric_analysis'], 
  ['Reproducibility assessment', 'reproducibility_assessment']
];

export const ReportsPage: React.FC = () => {
  const [reports, setReports] = useState<ReportResponse[]>([]);
  const [selected, setSelected] = useState<ReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const [experiments, setExperiments] = useState<any[]>([]);
  const [isGenerateModalOpen, setIsGenerateModalOpen] = useState(false);
  const [generatingFor, setGeneratingFor] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const list = await experimentApi.getReports();
        setReports(list);
        
        // Pre-fetch experiments for the generation modal
        const expList = await experimentApi.getExperiments();
        setExperiments(expList.items);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load reports.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleGenerateReport = async (experimentId: string) => {
    try {
      setGeneratingFor(experimentId);
      await experimentApi.startAiWorkflow(experimentId);
      // After starting the workflow, the report will be generated eventually.
      // We can redirect the user to the workflows page to watch the progress.
      window.location.href = '/workflows';
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start report generation workflow.');
      setGeneratingFor(null);
      setIsGenerateModalOpen(false);
    }
  };

  const openReport = async (report: ReportResponse) => {
    try {
      const details = await experimentApi.getReport(report.id);
      setSelected(details);
      setIsModalOpen(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load report details.');
    }
  };

  const getScoreColor = (score?: number) => {
    if (score == null) return { text: 'text-slate-400', border: 'border-slate-500/30', bg: 'bg-slate-500/10', glow: '' };
    if (score >= 80) return { text: 'text-emerald-400', border: 'border-emerald-500/50', bg: 'bg-emerald-500/10', glow: 'shadow-[0_0_15px_rgba(16,185,129,0.2)]' };
    if (score >= 60) return { text: 'text-orange-400', border: 'border-orange-500/50', bg: 'bg-orange-500/10', glow: 'shadow-[0_0_15px_rgba(249,115,22,0.2)]' };
    return { text: 'text-red-400', border: 'border-red-500/50', bg: 'bg-red-500/10', glow: 'shadow-[0_0_15px_rgba(239,68,68,0.2)]' };
  };

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return `Generated on ${d.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' })}`;
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-8 relative">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">Experiment Reports</h1>
          <p className="text-sm text-slate-400">Generate and download reproducibility reports.</p>
        </div>
        <button 
          onClick={() => setIsGenerateModalOpen(true)}
          className="flex items-center px-4 py-2.5 bg-brand-500 hover:bg-brand-400 text-white text-sm font-semibold rounded-xl transition-colors shadow-lg shadow-brand-500/20"
        >
          <Plus className="w-4 h-4 mr-2" />
          Generate Report
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-900/20 border border-red-500/30 text-red-400 rounded-xl text-sm flex items-center">
          <AlertCircle className="w-5 h-5 mr-3" />
          {error}
        </div>
      )}

      {loading ? (
        <div className="h-40 flex items-center justify-center text-slate-400">
          <Loader2 className="w-6 h-6 animate-spin mr-3 text-brand-500" />
          Loading Reports...
        </div>
      ) : reports.length === 0 ? (
        <div className="glass-panel p-12 text-center flex flex-col items-center justify-center">
          <FileText className="w-16 h-16 text-slate-600 mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">No Reports Generated Yet</h3>
          <p className="text-slate-400 mb-6">Run AI Analysis from an experiment to create a report.</p>
          <button 
            onClick={() => setIsGenerateModalOpen(true)}
            className="px-6 py-2.5 bg-brand-500/20 border border-brand-500/50 text-brand-400 hover:bg-brand-500/30 text-sm font-semibold rounded-xl transition-colors"
          >
            Start Analysis
          </button>
        </div>
      ) : (
        <div className="glass-panel p-4 sm:p-6 space-y-4">
          {reports.map(report => {
            const colors = getScoreColor(report.overall_score);
            const titleDisplay = report.experiment_title || report.title || report.experiment_id;
            // The mockup shows "EXP-2026-001" and then the name on a separate line
            const match = titleDisplay.match(/^(EXP-\d+-\d+)(?:\s+(?:\(Run \d+\)\s+)?-\s+(.*))?$/);
            const expId = match ? match[1] : (report.experiment_id || 'Experiment');
            const expName = match ? (match[2] || report.title) : titleDisplay;

            return (
              <div 
                key={report.id} 
                className="flex flex-col sm:flex-row items-center justify-between p-5 bg-slate-800/40 hover:bg-slate-800/60 transition-colors border border-slate-700/50 rounded-2xl gap-6"
              >
                <div className="flex-1 w-full">
                  <h3 className="font-bold text-white text-base">
                    {expId}
                  </h3>
                  <p className="text-sm text-slate-300 mt-1 font-medium">{expName}</p>
                  <p className="text-xs text-slate-500 mt-2">{formatDate(report.created_at)}</p>
                </div>

                <div className="flex items-center justify-end gap-6 w-full sm:w-auto">
                  
                  {/* Score Badge */}
                  <div className={`w-14 h-14 rounded-full border-2 flex items-center justify-center font-bold text-lg ${colors.border} ${colors.bg} ${colors.text} ${colors.glow}`}>
                    {report.overall_score ?? '—'}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-3">
                    <button 
                      onClick={() => openReport(report)}
                      className="px-6 py-2.5 rounded-xl border border-sky-500/30 bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 text-sm font-semibold transition-colors flex items-center shadow-inner"
                    >
                      View
                    </button>
                    <button 
                      className="px-6 py-2.5 rounded-xl border border-sky-500/30 bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 text-sm font-semibold transition-colors flex items-center shadow-inner"
                    >
                      Download
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Generate Report Modal */}
      {isGenerateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setIsGenerateModalOpen(false)} />
          <div className="relative w-full max-w-xl glass-panel flex flex-col overflow-hidden shadow-2xl rounded-2xl animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between p-6 border-b border-white/10">
              <div>
                <h2 className="text-xl font-bold text-white">Generate Report</h2>
                <p className="text-sm text-slate-400 mt-1">Select an experiment to run the AI reproducibility workflow.</p>
              </div>
              <button onClick={() => setIsGenerateModalOpen(false)} className="p-2 rounded-full hover:bg-white/10 text-slate-400 hover:text-white transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 max-h-[50vh] overflow-y-auto custom-scrollbar">
              {experiments.length === 0 ? (
                <p className="text-slate-400 text-sm text-center py-8">No experiments found. Upload one first!</p>
              ) : (
                <div className="space-y-3">
                  {experiments.map(exp => (
                    <div key={exp.id} className="flex items-center justify-between p-4 bg-slate-800/40 border border-slate-700/50 rounded-xl hover:bg-slate-800/60 transition-colors">
                      <div>
                        <p className="font-semibold text-white text-sm">{exp.title}</p>
                        <p className="text-xs text-slate-400 mt-1 font-mono">{exp.id}</p>
                      </div>
                      <button 
                        onClick={() => handleGenerateReport(exp.id)}
                        disabled={generatingFor === exp.id}
                        className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors shadow-lg ${
                          generatingFor === exp.id 
                            ? 'bg-slate-700 text-slate-400 cursor-not-allowed' 
                            : 'bg-brand-500 hover:bg-brand-400 text-white shadow-brand-500/20'
                        }`}
                      >
                        {generatingFor === exp.id ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Run Analysis'}
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Report Details Modal */}
      {isModalOpen && selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
          {/* Backdrop */}
          <div 
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setIsModalOpen(false)}
          />
          
          {/* Modal Content */}
          <div className="relative w-full max-w-4xl max-h-[85vh] glass-panel flex flex-col overflow-hidden shadow-2xl rounded-2xl animate-in fade-in zoom-in-95 duration-200">
            {/* Modal Header */}
            <div className="flex items-start justify-between p-6 border-b border-white/10 shrink-0">
              <div>
                <h2 className="text-xl font-bold text-white mb-1">{selected.title}</h2>
                <p className="text-sm text-slate-400">
                  Experiment: {selected.experiment_title || selected.experiment_id} · Analysis run: {selected.analysis_run_id.slice(0, 8)}
                </p>
              </div>
              <button 
                onClick={() => setIsModalOpen(false)}
                className="p-2 rounded-full hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-8 custom-scrollbar">
              
              <section>
                <h3 className="text-sm uppercase tracking-wider font-semibold text-slate-500 mb-3">Executive Summary</h3>
                <p className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">
                  {selected.structured_json?.executive_summary || selected.summary}
                </p>
              </section>

              <section>
                <h3 className="text-sm uppercase tracking-wider font-semibold text-slate-500 mb-3">Findings</h3>
                <div className="space-y-3">
                  {(selected.structured_json?.findings || []).map((finding, i) => (
                    <div key={i} className="p-4 bg-slate-900/60 rounded-xl border border-white/5">
                      <div className="flex items-center justify-between mb-2">
                        <p className="font-semibold text-slate-200">{finding.title}</p>
                        <span className={`text-xs px-2 py-0.5 rounded-md font-bold ${
                          finding.severity === 'HIGH' ? 'bg-red-500/20 text-red-400' :
                          finding.severity === 'MEDIUM' ? 'bg-orange-500/20 text-orange-400' :
                          'bg-emerald-500/20 text-emerald-400'
                        }`}>
                          {finding.severity}
                        </span>
                      </div>
                      <p className="text-sm text-slate-400 mb-2 leading-relaxed">{finding.observed_evidence}</p>
                      <p className="text-sm text-brand-300"><span className="font-medium text-brand-400">Recommendation:</span> {finding.recommendation}</p>
                    </div>
                  ))}
                  {(!selected.structured_json?.findings || selected.structured_json.findings.length === 0) && (
                     <p className="text-sm text-slate-500">No specific findings recorded.</p>
                  )}
                </div>
              </section>

              <section>
                <h3 className="text-sm uppercase tracking-wider font-semibold text-slate-500 mb-3">Actionable Recommendations</h3>
                <ul className="list-disc pl-5 space-y-2 text-sm text-slate-300">
                  {(selected.structured_json?.actionable_recommendations || []).map((item, i) => <li key={i} className="pl-1">{item}</li>)}
                </ul>
              </section>

              <section>
                <h3 className="text-sm uppercase tracking-wider font-semibold text-slate-500 mb-4">Detailed Sections</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {sections.map(([label, key]) => selected.structured_json?.[key] && (
                    <div key={key} className="p-4 bg-slate-800/40 rounded-xl border border-slate-700/50">
                      <p className="text-sm font-semibold text-brand-400 mb-2">{label}</p>
                      <p className="text-sm text-slate-300 leading-relaxed">{String(selected.structured_json[key])}</p>
                    </div>
                  ))}
                </div>
              </section>
              
            </div>
            
            {/* Modal Footer */}
            <div className="p-4 border-t border-white/10 shrink-0 bg-slate-900/50 flex justify-end">
               <button 
                  onClick={() => setIsModalOpen(false)}
                  className="px-6 py-2.5 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-sm font-semibold transition-colors"
                >
                  Close
                </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
