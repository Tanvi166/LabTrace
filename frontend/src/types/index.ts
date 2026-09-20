export interface ExperimentFile {
  id: string;
  original_filename: string;
  safe_filename: string;
  filename: string;
  file_type: string;
  content_type?: string;
  file_extension?: string;
  file_size_bytes: number;
  created_at: string;
}

export interface Experiment {
  id: string;
  title: string;
  description?: string;
  status: string;
  tags: string[];
  framework?: string;
  python_version?: string;
  reproducibility_score?: number;
  created_at: string;
  updated_at: string;
  files_count?: number;
  files?: ExperimentFile[];
}

export interface AgentLog {
  agent_name: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  execution_time: number;
  summary?: string;
  structured_output?: any;
}

export interface AgentRunStatus {
  run_id: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  agents: AgentLog[];
}

export interface RagResult {
  title: string;
  source: string;
  excerpt: string;
  relevance_score: number;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'RESEARCHER' | 'ADMIN';
}
