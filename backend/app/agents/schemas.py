from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.analysis.models import (
    ExtractedMetadata,
    CodeFileDiff,
    ConfigParamDiff,
    DependencyDiff,
    MetricSummary,
    MetricComparison,
    ReproducibilityEvaluation
)

# 1. Coordinator Schemas
class CoordinatorInput(BaseModel):
    experiment_a_id: str
    experiment_b_id: Optional[str] = None
    mode: str = "single"  # "single" or "compare"

class CoordinatorOutput(BaseModel):
    workflow_dag: List[str]
    dependencies: Dict[str, List[str]] = Field(default_factory=dict)
    mode: str
    status: str
    summary: str

# 2. Metadata Agent Schemas
class MetadataAgentInput(BaseModel):
    metadata_a: ExtractedMetadata
    metadata_b: Optional[ExtractedMetadata] = None
    mcp_metadata: Dict[str, Any] = Field(default_factory=dict)

class MetadataAgentOutput(BaseModel):
    summary: str
    detected_frameworks: List[str]
    detected_environment: str
    missing_metadata: List[str]
    important_differences: List[str]
    evidence_notes: List[str]

# 3. Code Analysis Agent Schemas
class CodeAgentInput(BaseModel):
    file_diffs: List[CodeFileDiff]
    config_diffs: List[ConfigParamDiff]
    dependency_diffs: List[DependencyDiff]
    mcp_files: Dict[str, Any] = Field(default_factory=dict)
    mcp_file_contents: List[Dict[str, Any]] = Field(default_factory=list)

class CodeAgentOutput(BaseModel):
    summary: str
    observed_code_changes: List[str]
    ast_function_modifications: List[str]
    configuration_changes: List[str]
    dependency_changes: List[str]
    interpretation: str

# 4. Results Analysis Agent Schemas
class ResultsAgentInput(BaseModel):
    metrics_a: List[MetricSummary]
    metrics_b: Optional[List[MetricSummary]] = None
    metric_comparisons: List[MetricComparison] = Field(default_factory=list)
    mcp_results: Dict[str, Any] = Field(default_factory=dict)

class ResultsAgentOutput(BaseModel):
    summary: str
    key_metrics_observed: List[str]
    best_performance_values: Dict[str, str]
    trajectory_analysis: str
    observed_performance_delta: Optional[str] = None

# 5. Reproducibility Agent Schemas
class ReproducibilityAgentInput(BaseModel):
    evaluation: ReproducibilityEvaluation
    comparison_delta: Optional[Dict[str, Any]] = None
    mcp_findings: Dict[str, Any] = Field(default_factory=dict)

class ReproducibilityAgentOutput(BaseModel):
    overall_score: float
    summary: str
    randomness_audit: str
    dependency_audit: str
    environment_audit: str
    dataset_audit: str
    configuration_audit: str
    documentation_audit: str
    severity_breakdown: Dict[str, int]
    actionable_recommendations: List[str]
    findings: List["ReportFindingItem"] = Field(default_factory=list)

class KnowledgeAgentInput(BaseModel):
    question: str
class KnowledgeEvidence(BaseModel):
    title: str
    source: str
    content: str
    chunk_id: str
    score: float
class KnowledgeAgentOutput(BaseModel):
    summary: str
    evidence: List[KnowledgeEvidence] = Field(default_factory=list)

# 6. Report Agent & Final Structured Report Schemas
class ReportFindingItem(BaseModel):
    title: str
    category: str
    severity: str
    observed_evidence: str
    interpretation: str
    recommendation: str

class StructuredReportOutput(BaseModel):
    title: str
    executive_summary: str
    experiment_overview: str
    environment_analysis: str
    code_and_config_differences: str
    results_and_metric_analysis: str
    reproducibility_assessment: str
    overall_score: float
    findings: List[ReportFindingItem] = Field(default_factory=list)
    actionable_recommendations: List[str] = Field(default_factory=list)
    evidence_sources: List[str] = Field(default_factory=list)
    markdown_content: str
    html_content: str
