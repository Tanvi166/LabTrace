import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { UploadCloud, FileText, CheckCircle2, AlertCircle, X, ArrowRight, Loader2 } from 'lucide-react';
import { experimentApi } from '../services/api';
import { Experiment } from '../types';

const ALLOWED_EXT = ['.py', '.ipynb', '.csv', '.tsv', '.json', '.yaml', '.yml', '.toml', '.txt', '.md', '.log', '.zip'];
const ALLOWED_NAMES = ['requirements.txt', 'environment.yml', 'pyproject.toml', 'readme.md'];

export const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [tagsStr, setTagsStr] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [validationError, setValidationError] = useState<string | null>(null);
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState<boolean>(false);
  const [createdExperiment, setCreatedExperiment] = useState<Experiment | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  const handleFileSelection = (filesList: FileList | null) => {
    if (!filesList) return;
    setValidationError(null);
    const newFiles: File[] = Array.from(filesList);

    for (const f of newFiles) {
      const ext = '.' + f.name.split('.').pop()?.toLowerCase();
      const lowerName = f.name.toLowerCase();
      if (!ALLOWED_EXT.includes(ext) && !ALLOWED_NAMES.includes(lowerName)) {
        setValidationError(`Unsupported file type '${ext}' for file '${f.name}'. Allowed: .py, .ipynb, .csv, .json, .yaml, .toml, requirements.txt, .zip`);
        return;
      }
    }
    setSelectedFiles(prev => [...prev, ...newFiles]);
  };

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setValidationError('Please enter an experiment title.');
      return;
    }
    if (selectedFiles.length === 0) {
      setValidationError('Please select at least one experiment artifact file to upload.');
      return;
    }

    setIsSubmitting(true);
    setApiError(null);
    setValidationError(null);

    try {
      const tags = tagsStr.split(',').map(t => t.trim()).filter(Boolean);
      // 1. Create experiment record
      const exp = await experimentApi.createExperiment({ title, description, tags });
      // 2. Upload files
      await experimentApi.uploadExperimentFiles(exp.id, selectedFiles);
      
      setCreatedExperiment(exp);
      setUploadSuccess(true);
    } catch (err: any) {
      setApiError(err.response?.data?.detail || 'Failed to upload experiment files');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Upload & Analyze Experiment</h1>
        <p className="text-sm text-slate-500 mt-1">Upload research code, parameters, requirements, metrics CSVs, or ZIP archives.</p>
      </div>

      {uploadSuccess && createdExperiment ? (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-8 text-center space-y-4 shadow-sm">
          <CheckCircle2 className="w-16 h-16 text-emerald-600 mx-auto" />
          <h2 className="text-2xl font-bold text-emerald-900">Experiment Uploaded Successfully!</h2>
          <p className="text-sm text-emerald-800 max-w-lg mx-auto">
            {selectedFiles.length} file(s) safely extracted and saved to your storage bucket.
          </p>
          <div className="bg-white p-4 rounded-lg border border-emerald-200 text-slate-700 text-xs font-mono max-w-md mx-auto">
            Status: <span className="font-semibold text-indigo-600">READY</span> &bull; Storage: <span className="font-semibold text-emerald-600">VERIFIED</span>
          </div>
          <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800 max-w-lg mx-auto">
            Notice: Multi-agent AI analysis pipeline will be enabled in the next phase (Phase 3).
          </div>
          <div className="pt-2 flex justify-center space-x-4">
            <Link
              to={`/experiments/${createdExperiment.id}`}
              className="inline-flex items-center px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg text-sm shadow-sm transition-colors space-x-2"
            >
              <span>View Experiment Details</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Metadata Section */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="font-semibold text-slate-900 text-md">1. Experiment Information</h3>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Experiment Title *</label>
              <input
                type="text"
                value={title}
                onChange={e => setTitle(e.target.value)}
                placeholder="e.g. PyTorch ResNet50 CIFAR-10 Baseline"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Description (Optional)</label>
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                placeholder="Brief summary of model architecture, dataset, or seed settings..."
                rows={2}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Tags (Comma-separated)</label>
              <input
                type="text"
                value={tagsStr}
                onChange={e => setTagsStr(e.target.value)}
                placeholder="vision, resnet, pytorch, cifar10"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          {/* File Upload Zone */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="font-semibold text-slate-900 text-md">2. Upload Experiment Artifacts</h3>
            
            <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:border-indigo-500 transition-colors relative bg-slate-50/50">
              <input
                type="file"
                multiple
                onChange={e => handleFileSelection(e.target.files)}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <UploadCloud className="w-10 h-10 text-indigo-500 mx-auto mb-2" />
              <p className="text-sm font-semibold text-slate-800">Drag & Drop files or click to browse</p>
              <p className="text-xs text-slate-500 mt-1">
                Supports .py, .ipynb, .csv, .json, .yaml, .toml, requirements.txt, and .zip archives
              </p>
            </div>

            {/* Validation & API Errors */}
            {validationError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{validationError}</span>
              </div>
            )}
            {apiError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{apiError}</span>
              </div>
            )}

            {/* Selected File List */}
            {selectedFiles.length > 0 && (
              <div className="space-y-2 pt-2">
                <p className="text-xs font-medium text-slate-700 uppercase tracking-wider">Selected Files ({selectedFiles.length})</p>
                <div className="divide-y divide-slate-100 border border-slate-200 rounded-lg max-h-48 overflow-y-auto bg-slate-50">
                  {selectedFiles.map((file, idx) => (
                    <div key={idx} className="px-3 py-2 flex items-center justify-between text-xs">
                      <div className="flex items-center space-x-2 truncate">
                        <FileText className="w-4 h-4 text-slate-400 flex-shrink-0" />
                        <span className="font-medium text-slate-800 truncate">{file.name}</span>
                        <span className="text-slate-400">({(file.size / 1024).toFixed(1)} KB)</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeFile(idx)}
                        className="text-slate-400 hover:text-red-500 p-1"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-medium text-sm rounded-xl shadow-md transition-colors flex items-center justify-center space-x-2"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Extracting & Uploading Experiment Artifacts...</span>
              </>
            ) : (
              <>
                <UploadCloud className="w-5 h-5" />
                <span>Create & Upload Experiment</span>
              </>
            )}
          </button>
        </form>
      )}
    </div>
  );
};
