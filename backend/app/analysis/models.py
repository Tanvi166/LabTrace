from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DetectedSeed(BaseModel):
    library: str  # python_random, numpy, torch_cpu, torch_cuda, tensorflow
    call: str
    value: Optional[str] = None
    file: str

class ExtractedHyperparameters(BaseModel):
    learning_rate: Optional[float] = None
    batch_size: Optional[int] = None
    epochs: Optional[int] = None
    optimizer: Optional[str] = None
    scheduler: Optional[str] = None
    loss_function: Optional[str] = None
    model_name: Optional[str] = None
    dataset_name: Optional[str] = None
    raw_params: Dict[str, Any] = Field(default_factory=dict)

class ExtractedMetadata(BaseModel):
    frameworks: List[str] = Field(default_factory=list)
    python_version: Optional[str] = None
    imports: List[str] = Field(default_factory=list)
    dependencies: Dict[str, str] = Field(default_factory=dict)
    seeds: List[DetectedSeed] = Field(default_factory=list)
    cuda_flags: List[str] = Field(default_factory=list)
    hyperparameters: ExtractedHyperparameters = Field(default_factory=ExtractedHyperparameters)

class CodeFunctionDiff(BaseModel):
    name: str
    file: str
    change_type: str  # added, removed, modified

class CodeFileDiff(BaseModel):
    filename: str
    change_type: str  # added, removed, modified, unchanged
    text_diff_lines: List[str] = Field(default_factory=list)
    ast_function_diffs: List[CodeFunctionDiff] = Field(default_factory=list)

class ConfigParamDiff(BaseModel):
    parameter: str
    experiment_a: Optional[Any] = None
    experiment_b: Optional[Any] = None
    change_type: str  # added, removed, changed, unchanged

class DependencyDiff(BaseModel):
    package: str
    version_a: Optional[str] = None
    version_b: Optional[str] = None
    change_type: str  # added, removed, version_changed, unchanged

class MetricSummary(BaseModel):
    metric_name: str
    min_value: float
    max_value: float
    mean_value: float
    std_value: float
    final_value: float
    best_value: float
    trajectory: List[Dict[str, Any]] = Field(default_factory=list)

class MetricComparison(BaseModel):
    metric_name: str
    experiment_a_final: float
    experiment_b_final: float
    experiment_a_best: float
    experiment_b_best: float
    absolute_diff: float
    relative_diff_pct: Optional[float] = None
    combined_trajectory: List[Dict[str, Any]] = Field(default_factory=list)

class ReproducibilityFinding(BaseModel):
    id: str
    category: str  # randomness, dependencies, environment, dataset, configuration, documentation
    severity: str  # HIGH, MEDIUM, LOW
    status: str    # PASSED, WARNING, FAILED
    title: str
    evidence: str
    recommendation: str

class ReproducibilityCategoryScore(BaseModel):
    category: str
    weight: float
    score: float  # 0.0 - 100.0
    passed_checks: int
    total_checks: int

class ReproducibilityEvaluation(BaseModel):
    overall_score: float  # 0.0 - 100.0
    category_scores: List[ReproducibilityCategoryScore] = Field(default_factory=list)
    findings: List[ReproducibilityFinding] = Field(default_factory=list)

class AnalysisResult(BaseModel):
    experiment_id: str
    status: str
    extracted_metadata: ExtractedMetadata
    reproducibility: ReproducibilityEvaluation
    metrics_summary: List[MetricSummary] = Field(default_factory=list)

class ComparisonResult(BaseModel):
    experiment_a_id: str
    experiment_b_id: str
    experiment_a_title: str
    experiment_b_title: str
    code_file_diffs: List[CodeFileDiff] = Field(default_factory=list)
    config_diffs: List[ConfigParamDiff] = Field(default_factory=list)
    dependency_diffs: List[DependencyDiff] = Field(default_factory=list)
    metric_comparisons: List[MetricComparison] = Field(default_factory=list)
    reproducibility_delta: Dict[str, Any] = Field(default_factory=dict)
