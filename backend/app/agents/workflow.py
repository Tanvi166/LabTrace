import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.experiment import Experiment, AnalysisRun
from app.models.report import Report
from app.models.agent_log import AgentLog
from app.models.user import User
from app.services.storage_service import get_storage_provider
from app.services.tool_provider import WorkflowMCPToolProvider

from app.analysis import (
    MetadataExtractorService,
    CodeAnalyzerService,
    ConfigDiffService,
    ResultsAnalyzerService,
    ReproducibilityEvaluatorService,
    ExperimentComparisonService
)

from app.agents.coordinator import CoordinatorAgent
from app.agents.metadata_agent import MetadataAgent
from app.agents.code_agent import CodeAnalysisAgent
from app.agents.results_agent import ResultsAnalysisAgent
from app.agents.reproducibility_agent import ReproducibilityAgent
from app.agents.knowledge_agent import KnowledgeAgent
from app.agents.report_agent import ReportAgent
from app.agents.report_agent import ReportAgentInput

from app.agents.schemas import (
    CoordinatorInput,
    MetadataAgentInput,
    CodeAgentInput,
    ResultsAgentInput,
    ReproducibilityAgentInput
    , KnowledgeAgentInput
)

class AgentWorkflowEngine:
    @staticmethod
    def run_workflow(
        experiment_id: str,
        compare_with_experiment_id: Optional[str] = None,
        db: Session = None,
        current_user: User = None,
    ) -> Dict[str, Any]:
        exp_a = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not exp_a:
            raise ValueError("Experiment A not found")

        exp_b = None
        if compare_with_experiment_id:
            exp_b = db.query(Experiment).filter(Experiment.id == compare_with_experiment_id).first()
            if not exp_b:
                raise ValueError("Experiment B not found")

        storage = get_storage_provider()
        start_time = time.time()

        # Create AnalysisRun entity
        analysis_run = AnalysisRun(
            experiment_id=exp_a.id,
            status="RUNNING",
            started_at=datetime.now(timezone.utc)
        )
        db.add(analysis_run)
        db.commit()
        db.refresh(analysis_run)

        try:
            if current_user is None:
                raise ValueError("A workflow user is required for MCP tool access")

            workflow_state = {
                "Coordinator Agent": {"depends_on": [], "status": "PENDING"},
                "Metadata Agent": {"depends_on": ["Coordinator Agent"], "status": "PENDING"},
                "Code Analysis Agent": {"depends_on": ["Metadata Agent"], "status": "PENDING"},
                "Results Agent": {"depends_on": ["Code Analysis Agent"], "status": "PENDING"},
                "Reproducibility Agent": {"depends_on": ["Results Agent"], "status": "PENDING"},
                "Knowledge Agent": {"depends_on": ["Reproducibility Agent"], "status": "PENDING"},
                "Report Agent": {"depends_on": ["Knowledge Agent"], "status": "PENDING"},
            }

            def mcp_call(agent_name: str, tool_name: str, arguments: dict, failures: list[str]) -> dict:
                try:
                    return WorkflowMCPToolProvider(
                        db, current_user, analysis_run.id, exp_a.id, agent_name
                    ).call(tool_name, arguments)
                except Exception as exc:
                    failures.append(f"{tool_name}: {exc}")
                    return {}

            def run_agent(agent_name: str, agent, input_data, mcp_failures: list[str]):
                dependencies = workflow_state[agent_name]["depends_on"]
                if any(workflow_state[name]["status"] in {"PENDING", "RUNNING"} for name in dependencies):
                    raise RuntimeError(f"{agent_name} dependencies are incomplete")
                workflow_state[agent_name]["status"] = "RUNNING"
                output = agent.run(input_data, analysis_run.id, db)
                if mcp_failures:
                    log = db.query(AgentLog).filter(
                        AgentLog.analysis_run_id == analysis_run.id,
                        AgentLog.agent_name == agent_name,
                    ).order_by(AgentLog.created_at.desc()).first()
                    log.status = "FAILED"
                    log.error_message = "; ".join(mcp_failures)
                    db.commit()
                    workflow_state[agent_name]["status"] = "FAILED"
                else:
                    workflow_state[agent_name]["status"] = "COMPLETED"
                return output

            # Download files for Exp A
            files_a: Dict[str, bytes] = {}
            fnames_a: list = []
            for f in exp_a.files:
                fnames_a.append(f.filename)
                if storage.file_exists(f.storage_path):
                    files_a[f.filename] = storage.download_file(f.storage_path)

            # Download files for Exp B if comparison
            files_b: Dict[str, bytes] = {}
            fnames_b: list = []
            if exp_b:
                for f in exp_b.files:
                    fnames_b.append(f.filename)
                    if storage.file_exists(f.storage_path):
                        files_b[f.filename] = storage.download_file(f.storage_path)

            # 1. Deterministic Phase 3 outputs
            meta_a = MetadataExtractorService.extract_from_files(files_a)
            meta_b = MetadataExtractorService.extract_from_files(files_b) if exp_b else None

            code_diffs = CodeAnalyzerService.compare_codebases(files_a, files_b) if exp_b else []
            config_diffs = ConfigDiffService.compare_configs(
                meta_a.hyperparameters.raw_params,
                meta_b.hyperparameters.raw_params if meta_b else {}
            ) if exp_b else []
            dep_diffs = ConfigDiffService.compare_dependencies(
                meta_a.dependencies,
                meta_b.dependencies if meta_b else {}
            ) if exp_b else []

            metrics_a = ResultsAnalyzerService.analyze_metrics(files_a)
            metrics_b = ResultsAnalyzerService.analyze_metrics(files_b) if exp_b else []
            metric_comps = ResultsAnalyzerService.compare_metrics(metrics_a, metrics_b) if exp_b else []

            repro_eval_a = ReproducibilityEvaluatorService.evaluate(meta_a, fnames_a, exp_a.description or "")

            # 2. Execute Agents Sequence with DB AgentLogs
            # Step 1: Coordinator
            coord = CoordinatorAgent()
            coord_out = run_agent("Coordinator Agent", coord, CoordinatorInput(
                experiment_a_id=exp_a.id,
                experiment_b_id=exp_b.id if exp_b else None,
                mode="compare" if exp_b else "single"
            ), [])

            # Step 2: Metadata Agent
            metadata_failures = []
            mcp_metadata = mcp_call("Metadata Agent", "get_experiment_metadata", {"experiment_id": exp_a.id}, metadata_failures)
            meta_agent = MetadataAgent()
            meta_out = run_agent("Metadata Agent", meta_agent, MetadataAgentInput(
                metadata_a=meta_a,
                metadata_b=meta_b,
                mcp_metadata=mcp_metadata,
            ), metadata_failures)

            # Step 3: Code Agent
            code_failures = []
            mcp_files = mcp_call("Code Analysis Agent", "get_experiment_files", {"experiment_id": exp_a.id}, code_failures)
            mcp_file_contents = []
            for file_info in mcp_files.get("files", []):
                if file_info.get("file_type") in {"code", "config", "env"}:
                    content = mcp_call("Code Analysis Agent", "get_file_content", {"experiment_id": exp_a.id, "file_id": file_info["id"]}, code_failures)
                    if content:
                        mcp_file_contents.append(content)
            code_agent = CodeAnalysisAgent()
            code_out = run_agent("Code Analysis Agent", code_agent, CodeAgentInput(
                file_diffs=code_diffs,
                config_diffs=config_diffs,
                dependency_diffs=dep_diffs,
                mcp_files=mcp_files,
                mcp_file_contents=mcp_file_contents,
            ), code_failures)

            # Step 4: Results Agent
            results_failures = []
            mcp_results = mcp_call("Results Agent", "get_experiment_results", {"experiment_id": exp_a.id}, results_failures)
            results_agent = ResultsAnalysisAgent()
            results_out = run_agent("Results Agent", results_agent, ResultsAgentInput(
                metrics_a=metrics_a,
                metrics_b=metrics_b if exp_b else None,
                metric_comparisons=metric_comps,
                mcp_results=mcp_results,
            ), results_failures)

            # Step 5: Reproducibility Agent
            reproducibility_failures = []
            mcp_findings = mcp_call("Reproducibility Agent", "get_reproducibility_findings", {"experiment_id": exp_a.id}, reproducibility_failures)
            repro_agent = ReproducibilityAgent()
            repro_out = run_agent("Reproducibility Agent", repro_agent, ReproducibilityAgentInput(
                evaluation=repro_eval_a,
                mcp_findings=mcp_findings,
            ), reproducibility_failures)

            knowledge_agent = KnowledgeAgent()
            knowledge_out = run_agent("Knowledge Agent", knowledge_agent, KnowledgeAgentInput(
                question="What reproducibility guidance applies to the observed deterministic experiment findings?"
            ), [])

            # Step 6: Report Agent
            report_agent = ReportAgent()
            report_out = run_agent("Report Agent", report_agent, ReportAgentInput(
                experiment_a_title=exp_a.title,
                experiment_b_title=exp_b.title if exp_b else "",
                metadata_out=meta_out,
                code_out=code_out,
                results_out=results_out,
                reproducibility_out=repro_out,
                knowledge_out=knowledge_out
            ), [])

            duration = round(time.time() - start_time, 2)

            # Persist Report model in DB
            db_report = Report(
                experiment_id=exp_a.id,
                analysis_run_id=analysis_run.id,
                title=report_out.title,
                summary=report_out.executive_summary,
                content_markdown=report_out.markdown_content,
                content_html=report_out.html_content,
                structured_json=report_out.model_dump()
            )
            db.add(db_report)
            db.commit()
            db.refresh(db_report)

            # Update AnalysisRun
            failed_steps = [name for name, step in workflow_state.items() if step["status"] == "FAILED"]
            analysis_run.status = "FAILED" if failed_steps else "COMPLETED"
            analysis_run.error_message = "; ".join(failed_steps) if failed_steps else None
            analysis_run.completed_at = datetime.now(timezone.utc)
            analysis_run.duration_seconds = duration
            analysis_run.overall_score = repro_eval_a.overall_score
            analysis_run.extracted_metadata = meta_a.model_dump()
            analysis_run.findings = [f.model_dump() for f in repro_eval_a.findings]

            # Update Experiment
            exp_a.reproducibility_score = repro_eval_a.overall_score
            exp_a.status = "COMPLETED"
            db.commit()

            return {
                "analysis_run_id": analysis_run.id,
                "status": analysis_run.status,
                "duration_seconds": duration,
                "overall_score": repro_eval_a.overall_score,
                "report_id": db_report.id,
                "report": report_out.model_dump()
            }

        except Exception as e:
            analysis_run.status = "FAILED"
            analysis_run.completed_at = datetime.now(timezone.utc)
            analysis_run.error_message = str(e)
            exp_a.status = "FAILED"
            db.commit()
            raise e
