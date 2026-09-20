import React, { useState, useEffect } from 'react';
import { FlaskConical, CheckCircle2, AlertTriangle, FileText, ArrowRight, Search, Trash2, Eye, RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';
import { experimentApi, PaginatedExperiments } from '../services/api';
import { Experiment } from '../types';

export const DashboardPage: React.FC = () => {
  const [data, setData] = useState<PaginatedExperiments | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  const fetchExperiments = async (searchQuery: string = '') => {
    setLoading(true);
    setError(null);
    try {
      const res = await experimentApi.getExperiments({ search: searchQuery });
      setData(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch experiments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchExperiments(search);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this experiment and all uploaded files?')) return;
    try {
      await experimentApi.deleteExperiment(id);
      fetchExperiments(search);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete experiment');
    }
  };

  const experiments = data?.items || [];
  const totalCount = data?.total || 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">Research experiment management and reproducibility analysis</p>
        </div>
        <Link
          to="/upload"
          className="inline-flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium shadow-sm transition-colors space-x-2 self-start"
        >
          <FlaskConical className="w-4 h-4" />
          <span>New Experiment</span>
        </Link>
      </div>

      {/* Overview Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
            <FlaskConical className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium uppercase">Total Experiments</p>
            <p className="text-2xl font-bold text-slate-900 mt-1">{totalCount}</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium uppercase">Avg Reproducibility</p>
            <p className="text-sm font-semibold text-slate-600 mt-1 bg-slate-100 px-2 py-0.5 rounded inline-block">No analyses yet</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-amber-50 text-amber-600 rounded-lg">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium uppercase">Pending Audits</p>
            <p className="text-2xl font-bold text-slate-900 mt-1">{experiments.filter(e => e.status !== 'COMPLETED').length}</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium uppercase">Files Stored</p>
            <p className="text-2xl font-bold text-slate-900 mt-1">
              {experiments.reduce((sum, e) => sum + (e.files_count || (e.files?.length || 0)), 0)}
            </p>
          </div>
        </div>
      </div>

      {/* Search & Actions Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-96">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search experiments by name or description..."
            className="w-full pl-9 pr-4 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <button
          onClick={() => fetchExperiments(search)}
          className="flex items-center space-x-1.5 px-3 py-2 text-xs font-medium text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Experiments List */}
      {loading ? (
        <div className="bg-white p-12 rounded-xl border border-slate-200 text-center text-slate-500">
          Loading experiments...
        </div>
      ) : error ? (
        <div className="bg-red-50 text-red-700 p-4 rounded-xl border border-red-200 text-sm">
          {error}
        </div>
      ) : experiments.length === 0 ? (
        <div className="bg-white p-12 rounded-xl border border-slate-200 shadow-sm text-center">
          <FlaskConical className="w-12 h-12 text-slate-400 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-slate-800">No Experiments Found</h3>
          <p className="text-sm text-slate-500 max-w-md mx-auto mt-1 mb-6">
            Upload PyTorch, TensorFlow, Python scripts, CSV metrics, or configuration files to create your first research experiment.
          </p>
          <Link
            to="/upload"
            className="inline-flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium shadow-sm transition-colors space-x-2"
          >
            <span>Upload & Analyze First Experiment</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {experiments.map((exp) => (
            <div key={exp.id} className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h3 className="font-semibold text-slate-900 text-lg leading-tight truncate">{exp.title}</h3>
                  <span className={`px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wider ${
                    exp.status === 'READY' ? 'bg-emerald-100 text-emerald-800' : 'bg-blue-100 text-blue-800'
                  }`}>
                    {exp.status}
                  </span>
                </div>
                {exp.description && (
                  <p className="text-sm text-slate-600 line-clamp-2 mb-4">{exp.description}</p>
                )}
                {exp.tags && exp.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-4">
                    {exp.tags.map((tag, idx) => (
                      <span key={idx} className="bg-slate-100 text-slate-600 text-xs px-2 py-0.5 rounded">
                        #{tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                <div>
                  <span className="font-medium text-slate-700">{exp.files_count || (exp.files?.length || 0)} files</span>
                  <span className="mx-1.5">&bull;</span>
                  <span>{new Date(exp.created_at).toLocaleDateString()}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Link
                    to={`/experiments/${exp.id}`}
                    className="p-1.5 text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 rounded transition-colors"
                    title="View Experiment"
                  >
                    <Eye className="w-4 h-4" />
                  </Link>
                  <button
                    onClick={(e) => handleDelete(exp.id, e)}
                    className="p-1.5 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                    title="Delete Experiment"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
