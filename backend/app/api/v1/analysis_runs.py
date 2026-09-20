from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.experiment import Experiment, AnalysisRun
from app.models.report import Report
from app.models.agent_log import AgentLog
from app.api.v1.deps import get_current_user

router = APIRouter()

@router.get("/{analysis_run_id}")
def get_analysis_run_status(
    analysis_run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    run = db.query(AnalysisRun).filter(AnalysisRun.id == analysis_run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")

    exp = db.query(Experiment).filter(Experiment.id == run.experiment_id).first()
    if exp and exp.user_id and exp.user_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="You do not have permission to view this analysis run")

    logs = db.query(AgentLog).filter(AgentLog.analysis_run_id == run.id, ~AgentLog.agent_name.like("MCP:%")).all()
    completed_agents = [l.agent_name for l in logs if l.status == "COMPLETED"]
    failed_agents = [l.agent_name for l in logs if l.status == "FAILED"]
    running_log = next((log for log in reversed(logs) if log.status == "RUNNING"), None)
    current_agent = running_log.agent_name if running_log else None

    report = db.query(Report).filter(Report.analysis_run_id == run.id).first()

    return {
        "analysis_run_id": run.id,
        "experiment_id": run.experiment_id,
        "status": run.status,
        "overall_score": run.overall_score,
        "duration_seconds": run.duration_seconds,
        "current_agent": current_agent,
        "completed_agents": completed_agents,
        "failed_agents": failed_agents,
        "report_id": report.id if report else None,
        "started_at": run.started_at.isoformat() if run.started_at else "",
        "completed_at": run.completed_at.isoformat() if run.completed_at else ""
    }

@router.get("/{analysis_run_id}/agents")
def get_analysis_run_agent_logs(
    analysis_run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    run = db.query(AnalysisRun).filter(AnalysisRun.id == analysis_run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")

    exp = db.query(Experiment).filter(Experiment.id == run.experiment_id).first()
    if exp and exp.user_id and exp.user_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="You do not have permission to view this analysis run")

    logs = db.query(AgentLog).filter(AgentLog.analysis_run_id == run.id, ~AgentLog.agent_name.like("MCP:%")).order_by(AgentLog.created_at.asc()).all()

    return [
        {
            "id": l.id,
            "analysis_run_id": run.id,
            "experiment_id": run.experiment_id,
            "agent_name": l.agent_name,
            "status": l.status,
            "execution_time_seconds": l.execution_time_seconds,
            "summary": l.summary,
            "input_summary": (l.structured_output or {}).get("input_summary"),
            "output_summary": l.summary,
            "structured_output": l.structured_output,
            "error_message": l.error_message,
            "created_at": l.created_at.isoformat() if l.created_at else "",
            "completed_at": l.completed_at.isoformat() if l.completed_at else ""
        } for l in logs
    ]

@router.get("/{analysis_run_id}/report")
def get_analysis_run_report(
    analysis_run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    run = db.query(AnalysisRun).filter(AnalysisRun.id == analysis_run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")

    exp = db.query(Experiment).filter(Experiment.id == run.experiment_id).first()
    if exp and exp.user_id and exp.user_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="You do not have permission to view this report")

    report = db.query(Report).filter(Report.analysis_run_id == run.id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not generated for this analysis run")

    return {
        "id": report.id,
        "experiment_id": report.experiment_id,
        "analysis_run_id": report.analysis_run_id,
        "title": report.title,
        "summary": report.summary,
        "content_markdown": report.content_markdown,
        "content_html": report.content_html,
        "structured_json": report.structured_json,
        "created_at": report.created_at.isoformat() if report.created_at else ""
    }
