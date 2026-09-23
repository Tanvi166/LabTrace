import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, FileText, Trash2, Eye, Calendar, Tag, HardDrive, Cpu, AlertTriangle, X, CheckCircle2, Play, Loader2, Award, ShieldCheck, AlertCircle } from 'lucide-react';
import { experimentApi, FileContent, AnalysisResponse, AiWorkflowResponse, ReportResponse } from '../services/api';
import { Experiment, ExperimentFile } from '../types';

export const ExperimentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [experiment, setExperiment] = useState<Experiment | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Analysis state
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [aiResult, setAiResult] = useState<AiWorkflowResponse | null>(null);
  const [aiReport, setAiReport] = useState<ReportResponse | null>(null);
  const [aiAnalyzing, setAiAnalyzing] = useState<boolean>(false);

  // File Content Viewer Modal State
  const [selectedFile, setSelectedFile] = useState<ExperimentFile | null>(null);
  const [fileContent, setFileContent] = useState<FileContent | null>(null);
  const [contentLoading, setContentLoading] = useState<boolean>(false);

  const fetchDetail = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const data = await experimentApi.getExperiment(id);
      setExperiment(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load experiment');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [id]);

  const handleRunAnalysis = async () => {
    if (!id) return;
    setAnalyzing(true);
    setAnalysisError(null);
    try {
      const res = await experimentApi.analyzeExperiment(id);
      setAnalysisResult(res);
      fetchDetail();
    } catch (err: any) {
      setAnalysisError(err.response?.data?.detail || 'Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleRunAiAnalysis = async () => {
    if (!id) return;
    setAiAnalyzing(true); setAnalysisError(null);
    try {
      const result = await experimentApi.startAiAnalysis(id);
      setAiResult(result);
      setAiReport(await experimentApi.getReport(result.report_id));
      fetchDetail();
    } catch (err: any) {
      setAnalysisError(err.response?.data?.detail || 'AI analysis failed');
    } finally { setAiAnalyzing(false); }
  };

  const handleOpenFile = async (file: ExperimentFile) => {
    if (!id) return;
    setSelectedFile(file);
    setContentLoading(true);
    setFileContent(null);
    try {
      const res = await experimentApi.getFileContent(id, file.id);
      setFileContent(res);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to fetch file content');
    } finally {
      setContentLoading(false);
    }
  };

  const handleDeleteFile = async (fileId: string) => {
    if (!id) return;
    if (!confirm('Are you sure you want to delete this file?')) return;
    try {
      await experimentApi.deleteExperimentFile(id, fileId);
      if (selectedFile?.id === fileId) {
        setSelectedFile(null);
        setFileContent(null);
      }
      fetchDetail();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete file');
    }
  };

  const handleDeleteExperiment = async () => {
    if (!id) return;
    if (!confirm('Are you sure you want to delete this entire experiment and all stored files?')) return;
    try {
      await experimentApi.deleteExperiment(id);
      navigate('/');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete experiment');
    }
  };

  if (loading) {
    return <div className="p-12 text-center text-slate-500">Loading experiment details...</div>;
  }

  if (error || !experiment) {
    return (
      <div className="space-y-4">
        <Link to="/" className="inline-flex items-center text-sm text-indigo-600 hover:text-indigo-800 space-x-1">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </Link>
        <div className="p-4 bg-red-50 text-red-700 rounded-xl border border-red-200 text-sm">
          {error || 'Experiment not found'}
        </div>
      </div>
    );
  }

  const files = experiment.files || [];
  const score = analysisResult?.reproducibility?.overall_score ?? experiment.reproducibility_score;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <Link to="/" className="inline-flex items-center text-xs text-brand-400 hover:text-neon-cyan space-x-1 mb-1 transition-colors">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Dashboard</span>
          </Link>
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-bold text-white text-glow">{experiment.title}</h1>
            <span className={`px-2.5 py-0.5 rounded text-xs font-semibold uppercase tracking-wider ${
              experiment.status === 'COMPLETED' ? 'bg-emerald-100 text-emerald-800' : 'bg-blue-100 text-blue-800'
            }`}>
              {experiment.status}
            </span>
          </div>
          {experiment.description && <p className="text-sm text-slate-500">{experiment.description}</p>}
        </div>

        <div className="flex items-center space-x-3 self-start">
          <button
            onClick={handleRunAnalysis}
            disabled={analyzing || files.length === 0}
            className="inline-flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors space-x-2"
          >
            {analyzing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Running Analysis...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                <span>Run Deterministic Analysis</span>
              </>
            )}
          </button>
          <button
            onClick={handleRunAiAnalysis}
            disabled={aiAnalyzing || files.length === 0}
            className="inline-flex items-center px-4 py-2 bg-violet-600 hover:bg-violet-700 disabled:bg-violet-400 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors space-x-2"
          >
            {aiAnalyzing ? <><Loader2 className="w-4 h-4 animate-spin" /><span>Running AI Analysis...</span></> : <><Play className="w-4 h-4" /><span>Run AI Analysis</span></>}
          </button>
          <button
            onClick={handleDeleteExperiment}
            className="p-2 bg-red-50 hover:bg-red-100 text-red-700 rounded-lg border border-red-200 transition-colors"
            title="Delete Experiment"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {analysisError && (
        <div className="p-4 bg-red-50 text-red-700 rounded-xl border border-red-200 text-sm">
          {analysisError}
        </div>
      )}

      {aiResult && (
        <div className="bg-violet-50 border border-violet-200 rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between"><h3 className="font-bold text-violet-950">AI analysis {aiResult.status.toLowerCase()}</h3><span className="font-bold text-violet-800">Reproducibility score: {aiResult.overall_score}/100</span></div>
          <p className="text-sm text-violet-900">Completed agents: Coordinator, Metadata, Code Analysis, Results, Reproducibility, and Report. Run ID: {aiResult.analysis_run_id}</p>
          {aiReport && <><p className="text-sm font-semibold text-violet-950">{aiReport.structured_json?.executive_summary || aiReport.summary}</p><div className="text-sm"><p className="font-semibold text-violet-950">Key findings</p><ul className="list-disc pl-5 text-violet-900">{(aiReport.structured_json?.findings || []).map((f, i) => <li key={i}>{f.title}: {f.observed_evidence}</li>)}</ul><p className="font-semibold text-violet-950 mt-2">Recommendations</p><ul className="list-disc pl-5 text-violet-900">{(aiReport.structured_json?.actionable_recommendations || []).map((r, i) => <li key={i}>{r}</li>)}</ul></div></>}
        </div>
      )}

      {/* Overview Metadata Bar */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
        <div>
          <span className="text-slate-400 block mb-0.5">Created Date</span>
          <span className="font-semibold text-slate-800 flex items-center space-x-1">
            <Calendar className="w-3.5 h-3.5 text-slate-400" />
            <span>{new Date(experiment.created_at).toLocaleString()}</span>
          </span>
        </div>
        <div>
          <span className="text-slate-400 block mb-0.5">ML Framework</span>
          <span className="font-semibold text-slate-800 flex items-center space-x-1">
            <Cpu className="w-3.5 h-3.5 text-slate-400" />
            <span>{experiment.framework || 'Generic Python'}</span>
          </span>
        </div>
        <div>
          <span className="text-slate-400 block mb-0.5">Artifact Files</span>
          <span className="font-semibold text-slate-800 flex items-center space-x-1">
            <HardDrive className="w-3.5 h-3.5 text-slate-400" />
            <span>{files.length} Files</span>
          </span>
        </div>
        <div>
          <span className="text-slate-400 block mb-0.5">Reproducibility Score</span>
          {score !== undefined && score !== null ? (
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded font-bold text-xs ${
              score >= 80 ? 'bg-emerald-100 text-emerald-800' : score >= 50 ? 'bg-amber-100 text-amber-800' : 'bg-red-100 text-red-800'
            }`}>
              <Award className="w-3.5 h-3.5 mr-1" />
              {score} / 100
            </span>
          ) : (
            <span className="font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
              Pending Analysis
            </span>
          )}
        </div>
      </div>

      {/* Analysis Results Dashboard (If Available) */}
      {analysisResult && (
        <div className="space-y-6">
          {/* Category Scores Grid */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-900 text-base flex items-center space-x-2">
              <ShieldCheck className="w-5 h-5 text-indigo-600" />
              <span>Reproducibility Evaluation Breakdown</span>
            </h3>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              {analysisResult.reproducibility.category_scores.map((cat, idx) => (
                <div key={idx} className="bg-slate-50 p-3 rounded-lg border border-slate-200 text-center space-y-1">
                  <p className="text-[11px] font-semibold text-slate-500 uppercase">{cat.category}</p>
                  <p className="text-lg font-bold text-slate-900">{cat.score.toFixed(0)}%</p>
                  <p className="text-[10px] text-slate-400">{cat.passed_checks} / {cat.total_checks} passed</p>
                </div>
              ))}
            </div>
          </div>

          {/* Reproducibility Findings Checklist */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-900 text-base">Reproducibility Audit Findings</h3>
            <div className="divide-y divide-slate-100 border border-slate-200 rounded-lg overflow-hidden">
              {analysisResult.reproducibility.findings.map((item) => (
                <div key={item.id} className="p-4 space-y-1.5 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-800 text-sm flex items-center space-x-2">
                      {item.status === 'PASSED' ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      ) : item.status === 'WARNING' ? (
                        <AlertCircle className="w-4 h-4 text-amber-500" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 text-red-500" />
                      )}
                      <span>{item.title}</span>
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      item.status === 'PASSED' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                    }`}>
                      {item.status}
                    </span>
                  </div>
                  <p className="text-slate-600 font-mono bg-slate-50 p-2 rounded border border-slate-100">{item.evidence}</p>
                  <p className="text-slate-500 italic">Recommendation: {item.recommendation}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Artifact Files List */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-slate-900 text-base">Artifact Files ({files.length})</h3>
          <span className="text-xs text-slate-400">Click any file to inspect content</span>
        </div>

        {files.length === 0 ? (
          <div className="text-center py-8 text-slate-400 text-sm">No files uploaded for this experiment.</div>
        ) : (
          <div className="divide-y divide-slate-100 border border-slate-200 rounded-lg overflow-hidden">
            {files.map((file) => (
              <div key={file.id} className="p-3 hover:bg-slate-50 flex items-center justify-between text-xs transition-colors">
                <div className="flex items-center space-x-3 truncate">
                  <FileText className="w-4 h-4 text-indigo-500 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-slate-800 truncate">{file.filename}</p>
                    <p className="text-slate-400 text-[11px]">
                      {(file.file_size_bytes / 1024).toFixed(1)} KB &bull; Type: <span className="uppercase">{file.file_type}</span>
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleOpenFile(file)}
                    className="px-2.5 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-medium rounded transition-colors flex items-center space-x-1"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>View</span>
                  </button>
                  <button
                    onClick={() => handleDeleteFile(file.id)}
                    className="p-1 text-slate-400 hover:text-red-600 rounded transition-colors"
                    title="Delete File"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* File Content Viewer Modal */}
      {selectedFile && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-4xl max-h-[85vh] flex flex-col overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div className="flex items-center space-x-2 truncate">
                <FileText className="w-5 h-5 text-indigo-600 flex-shrink-0" />
                <h3 className="font-semibold text-slate-800 text-sm truncate">{selectedFile.filename}</h3>
                {fileContent?.is_truncated && (
                  <span className="px-2 py-0.5 bg-amber-100 text-amber-800 text-[10px] font-bold rounded uppercase">Truncated</span>
                )}
              </div>
              <button
                onClick={() => { setSelectedFile(null); setFileContent(null); }}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 flex-1 overflow-y-auto font-mono text-xs bg-slate-900 text-slate-200 leading-relaxed">
              {contentLoading ? (
                <div className="text-center py-12 text-slate-400">Loading file content...</div>
              ) : fileContent?.is_binary ? (
                <div className="text-center py-12 text-slate-400">Binary file format — preview unavailable for browser display.</div>
              ) : (
                <pre className="whitespace-pre-wrap font-mono">{fileContent?.content || 'Empty file'}</pre>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
