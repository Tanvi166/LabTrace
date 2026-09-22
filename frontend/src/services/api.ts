import axios from 'axios';
import { Experiment, ExperimentFile } from '../types';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('labtrace_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface PaginatedExperiments {
  total: number;
  page: number;
  page_size: number;
  items: Experiment[];
}

export interface FileContent {
  id: string;
  filename: string;
  file_type: string;
  content_type: string;
  file_size_bytes: number;
  content: string | null;
  is_binary: boolean;
  is_truncated: boolean;
}

export interface AnalysisResponse {
  experiment_id: string;
  status: string;
  duration_seconds: number;
  overall_score: number;
  extracted_metadata: {
    frameworks: string[];
    python_version: string;
    imports: string[];
    dependencies: Record<string, string>;
    seeds: Array<{ library: string; call: string; value?: string; file: string }>;
    cuda_flags: string[];
    hyperparameters: {
      learning_rate?: number;
      batch_size?: number;
      epochs?: number;
      optimizer?: string;
      scheduler?: string;
      model_name?: string;
      dataset_name?: string;
      raw_params: Record<string, any>;
    };
  };
  reproducibility: {
    overall_score: number;
    category_scores: Array<{
      category: string;
      weight: number;
      score: number;
      passed_checks: number;
      total_checks: number;
    }>;
    findings: Array<{
      id: string;
      category: string;
      severity: string;
      status: string;
      title: string;
      evidence: string;
      recommendation: string;
    }>;
  };
  metrics_summary: Array<{
    metric_name: string;
    min_value: number;
    max_value: number;
    mean_value: number;
    std_value: number;
    final_value: number;
    best_value: number;
    trajectory: Array<{ step: number; value: number }>;
  }>;
}

export interface ComparisonResponse {
  experiment_a_id: string;
  experiment_b_id: string;
  experiment_a_title: string;
  experiment_b_title: string;

  code_file_diffs: Array<{
    filename: string;
    change_type: string;
    text_diff_lines: string[];
    ast_function_diffs: Array<{ name: string; file: string; change_type: string }>;
  }>;
  config_diffs: Array<{
    parameter: string;
    experiment_a: any;
    experiment_b: any;
    change_type: string;
  }>;
  dependency_diffs: Array<{
    package: string;
    version_a?: string;
    version_b?: string;
    change_type: string;
  }>;
  metric_comparisons: Array<{
    metric_name: string;
    experiment_a_final: number;
    experiment_b_final: number;
    experiment_a_best: number;
    experiment_b_best: number;
    absolute_diff: number;
    relative_diff_pct?: number;
    combined_trajectory: Array<{ step: number; exp_a?: number; exp_b?: number }>;
  }>;
  reproducibility_delta: {
    experiment_a_score: number;
    experiment_b_score: number;
    score_diff: number;
    findings_a_count: number;
    findings_b_count: number;
  };
}

export interface ReportFinding {
  title: string;
  category: string;
  severity: string;
  observed_evidence: string;
  interpretation: string;
  recommendation: string;
}

export interface ReportResponse {
  id: string;
  experiment_id: string;
  experiment_title?: string;
  analysis_run_id: string;
  title: string;
  summary: string;
  overall_score?: number | null;
  content_markdown?: string;
  content_html?: string;
  structured_json?: {
    executive_summary?: string;
    overall_score?: number;
    findings?: ReportFinding[];
    actionable_recommendations?: string[];
    experiment_overview?: string;
    environment_analysis?: string;
    code_and_config_differences?: string;
    results_and_metric_analysis?: string;
    reproducibility_assessment?: string;
  };
  created_at: string;
}

export interface AgentRunStatus {
  analysis_run_id: string;
  experiment_id: string;
  experiment_title: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  overall_score?: number | null;
  duration_seconds?: number | null;
  started_at: string;
  completed_at: string;
  agent_count: number;
  completed_agents: string[];
  failed_agents: string[];
}

export interface AgentLog {
  agent_name: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  execution_time_seconds?: number | null;
  summary?: string | null;
  error_message?: string | null;
}

export interface AgentRunDetail extends AgentRunStatus {
  agents: Array<{
    agent_name: string;
    status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
    execution_time_seconds?: number | null;
    summary?: string | null;
    error_message?: string | null;
  }>;
}

export interface AiWorkflowResponse {
  analysis_run_id: string;
  status: string;
  duration_seconds: number;
  overall_score: number;
  report_id: string;
}
export interface KnowledgeResult { title: string; content: string; source: string; score: number; chunk_id: string; document_id: string; section?: string; }

export const experimentApi = {
  createExperiment: async (data: { title: string; description?: string; tags?: string[] }): Promise<Experiment> => {
    const res = await api.post<Experiment>('/experiments', data);
    return res.data;
  },

  getExperiments: async (params?: { page?: number; page_size?: number; search?: string }): Promise<PaginatedExperiments> => {
    const res = await api.get<PaginatedExperiments>('/experiments', { params });
    return res.data;
  },

  getExperiment: async (id: string): Promise<Experiment> => {
    const res = await api.get<Experiment>(`/experiments/${id}`);
    return res.data;
  },

  updateExperiment: async (id: string, data: { title?: string; description?: string; tags?: string[] }): Promise<Experiment> => {
    const res = await api.patch<Experiment>(`/experiments/${id}`, data);
    return res.data;
  },

  deleteExperiment: async (id: string): Promise<void> => {
    await api.delete(`/experiments/${id}`);
  },

  uploadExperimentFiles: async (id: string, files: File[]): Promise<ExperimentFile[]> => {
    const formData = new FormData();
    files.forEach((f) => formData.append('files', f));
    const res = await api.post<ExperimentFile[]>(`/experiments/${id}/files`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  getExperimentFiles: async (id: string): Promise<ExperimentFile[]> => {
    const res = await api.get<ExperimentFile[]>(`/experiments/${id}/files`);
    return res.data;
  },

  getFileContent: async (experimentId: string, fileId: string): Promise<FileContent> => {
    const res = await api.get<FileContent>(`/experiments/${experimentId}/files/${fileId}`);
    return res.data;
  },

  deleteExperimentFile: async (experimentId: string, fileId: string): Promise<void> => {
    await api.delete(`/experiments/${experimentId}/files/${fileId}`);
  },

  analyzeExperiment: async (id: string): Promise<AnalysisResponse> => {
    const res = await api.post<AnalysisResponse>(`/experiments/${id}/analyze`);
    return res.data;
  },

  startAiAnalysis: async (id: string): Promise<AiWorkflowResponse> => {
    const res = await api.post<AiWorkflowResponse>(`/experiments/${id}/ai-analyze`);
    return res.data;
  },

  compareExperiments: async (expAId: string, expBId: string): Promise<ComparisonResponse> => {
    const res = await api.post<ComparisonResponse>('/compare', {
      experiment_a_id: expAId,
      experiment_b_id: expBId,
    });
    return res.data;
  },

  startAiComparison: async (expAId: string, expBId: string): Promise<AiWorkflowResponse> => {
    const res = await api.post<AiWorkflowResponse>('/compare/ai', {
      experiment_a_id: expAId,
      experiment_b_id: expBId,
    });
    return res.data;
  },

  getAnalysisRun: async (id: string) => {
    const res = await api.get(`/analysis-runs/${id}`);
    return res.data;
  },

  getAnalysisRunAgents: async (id: string): Promise<AgentLog[]> => {
    const res = await api.get<AgentLog[]>(`/analysis-runs/${id}/agents`);
    return res.data;
  },

  getAgentRuns: async (): Promise<AgentRunStatus[]> => {
    const res = await api.get<AgentRunStatus[]>('/agents/runs');
    return res.data;
  },

  getAgentRun: async (id: string): Promise<AgentRunDetail> => {
    const res = await api.get<AgentRunDetail>(`/agents/runs/${id}`);
    return res.data;
  },

  getReports: async (): Promise<ReportResponse[]> => {
    const res = await api.get<ReportResponse[]>('/reports');
    return res.data;
  },

  getReport: async (id: string): Promise<ReportResponse> => {
    const res = await api.get<ReportResponse>(`/reports/${id}`);
    return res.data;
  },
  
  searchKnowledge: async (query: string, top_k = 5, mode = 'hybrid'): Promise<KnowledgeResult[]> => {
    const res = await api.post<{ results: KnowledgeResult[] }>('/rag/search', { query, top_k, mode }); return res.data.results;
  },
  chat: async (question: string): Promise<ChatResponse> => {
  const res = await api.post<ChatResponse>('/chat', { question });
  return res.data;
  },
  getRagStatus: async () => { const res = await api.get('/rag/status'); return res.data; },
  getMcpStatus: async () => { const res = await api.get('/mcp/status'); return res.data; },
  getMcpTools: async () => { const res = await api.get('/mcp/tools'); return res.data.tools; },
  getMcpCalls: async () => { const res = await api.get('/mcp/calls'); return res.data.calls; },
};
export interface ChatSource {
  title: string;
  chunk_id: string;
  score: number;
}

export interface ChatResponse {
  question: string;
  answer: string;
  sources: ChatSource[];
}
export default api;
