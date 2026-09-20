"""Shared, safe LabTrace tool implementations used by HTTP and MCP transports."""
from __future__ import annotations
from typing import Any
from sqlalchemy.orm import Session
from app.models.experiment import Experiment, ExperimentFile, AnalysisRun
from app.models.user import User
from app.services.storage_service import get_storage_provider
from app.analysis import MetadataExtractorService, ResultsAnalyzerService, ConfigDiffService, ReproducibilityEvaluatorService

TOOL_DEFINITIONS = [
    {"name":"get_experiment_metadata", "description":"Return safe experiment metadata.", "input_schema":{"experiment_id":{"type":"string"}}},
    {"name":"get_experiment_files", "description":"List safe file metadata for an experiment.", "input_schema":{"experiment_id":{"type":"string"}}},
    {"name":"get_file_content", "description":"Read a permitted stored file, limited to 300 KB.", "input_schema":{"experiment_id":{"type":"string"},"file_id":{"type":"string"}}},
    {"name":"get_experiment_results", "description":"Return deterministic metric summaries and persisted reproducibility results.", "input_schema":{"experiment_id":{"type":"string"}}},
    {"name":"compare_experiment_config", "description":"Compare deterministic extracted configuration and dependencies.", "input_schema":{"experiment_a_id":{"type":"string"},"experiment_b_id":{"type":"string"}}},
    {"name":"get_reproducibility_findings", "description":"Return deterministic reproducibility score and findings.", "input_schema":{"experiment_id":{"type":"string"}}},
]

def _experiment(db: Session, user: User, experiment_id: str) -> Experiment:
    if not isinstance(experiment_id, str) or not experiment_id.strip(): raise ValueError("experiment_id is required")
    exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not exp: raise LookupError("Experiment not found")
    if user.role != "ADMIN" and exp.user_id and exp.user_id != user.id: raise PermissionError("You do not have permission to access this experiment")
    return exp

def _files(exp: Experiment) -> dict[str, bytes]:
    storage = get_storage_provider(); result = {}
    for record in exp.files:
        if storage.file_exists(record.storage_path): result[record.filename] = storage.download_file(record.storage_path)
    return result

def invoke_tool(name: str, arguments: dict[str, Any], db: Session, user: User) -> dict[str, Any]:
    if not isinstance(arguments, dict): raise ValueError("Tool arguments must be an object")
    if name == "get_experiment_metadata":
        exp = _experiment(db, user, arguments.get("experiment_id")); return {"experiment_id":exp.id,"title":exp.title,"description":exp.description,"tags":exp.tags or [],"created_at":exp.created_at.isoformat() if exp.created_at else None,"owner_id":exp.user_id}
    if name == "get_experiment_files":
        exp = _experiment(db, user, arguments.get("experiment_id")); return {"experiment_id":exp.id,"files":[{"id":f.id,"filename":f.filename,"size":f.file_size_bytes,"content_type":f.content_type,"file_type":f.file_type} for f in exp.files]}
    if name == "get_file_content":
        exp = _experiment(db, user, arguments.get("experiment_id")); file_id = arguments.get("file_id")
        if not isinstance(file_id, str) or not file_id: raise ValueError("file_id is required")
        record = db.query(ExperimentFile).filter(ExperimentFile.id == file_id, ExperimentFile.experiment_id == exp.id).first()
        if not record: raise LookupError("File not found")
        raw = get_storage_provider().download_file(record.storage_path); limit = 300 * 1024
        try: content = raw[:limit].decode("utf-8"); binary = False
        except UnicodeDecodeError: content = None; binary = True
        return {"experiment_id":exp.id,"file_id":record.id,"filename":record.filename,"content":content,"is_binary":binary,"is_truncated":len(raw)>limit}
    if name == "get_experiment_results":
        exp = _experiment(db, user, arguments.get("experiment_id")); files = _files(exp)
        latest = db.query(AnalysisRun).filter(AnalysisRun.experiment_id == exp.id).order_by(AnalysisRun.created_at.desc()).first()
        return {"experiment_id":exp.id,"metrics":[item.model_dump() for item in ResultsAnalyzerService.analyze_metrics(files)],"overall_score":latest.overall_score if latest else exp.reproducibility_score,"findings":latest.findings if latest else []}
    if name == "compare_experiment_config":
        a = _experiment(db, user, arguments.get("experiment_a_id")); b = _experiment(db, user, arguments.get("experiment_b_id")); ma = MetadataExtractorService.extract_from_files(_files(a)); mb = MetadataExtractorService.extract_from_files(_files(b))
        return {"experiment_a_id":a.id,"experiment_b_id":b.id,"config_diffs":[x.model_dump() for x in ConfigDiffService.compare_configs(ma.hyperparameters.raw_params, mb.hyperparameters.raw_params)],"dependency_diffs":[x.model_dump() for x in ConfigDiffService.compare_dependencies(ma.dependencies, mb.dependencies)]}
    if name == "get_reproducibility_findings":
        exp = _experiment(db, user, arguments.get("experiment_id")); files = _files(exp); metadata = MetadataExtractorService.extract_from_files(files); evaluation = ReproducibilityEvaluatorService.evaluate(metadata, [f.filename for f in exp.files], exp.description or "")
        return {"experiment_id":exp.id,"overall_score":evaluation.overall_score,"findings":[item.model_dump() for item in evaluation.findings]}
    raise ValueError(f"Unknown MCP tool: {name}")
