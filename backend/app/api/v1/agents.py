from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.experiment import Experiment, AnalysisRun
from app.models.agent_log import AgentLog
from app.api.v1.deps import get_current_user

router = APIRouter()


@router.get("/runs")
def list_analysis_runs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all analysis runs accessible to the current user, with agent progress summaries."""
    if current_user.role == "ADMIN":
        runs = db.query(AnalysisRun).join(AgentLog).filter(~AgentLog.agent_name.like("MCP:%")).distinct().order_by(AnalysisRun.created_at.desc()).limit(50).all()
    else:
        runs = (
            db.query(AnalysisRun)
            .join(Experiment, AnalysisRun.experiment_id == Experiment.id)
            .join(AgentLog, AgentLog.analysis_run_id == AnalysisRun.id)
            .filter(Experiment.user_id == current_user.id)
            .filter(~AgentLog.agent_name.like("MCP:%"))
            .distinct()
            .order_by(AnalysisRun.created_at.desc())
            .limit(50)
            .all()
        )

    results = []
    for run in runs:
        logs = db.query(AgentLog).filter(AgentLog.analysis_run_id == run.id, ~AgentLog.agent_name.like("MCP:%")).order_by(AgentLog.created_at.asc()).all()
        exp = db.query(Experiment).filter(Experiment.id == run.experiment_id).first()
        results.append({
            "analysis_run_id": run.id,
            "experiment_id": run.experiment_id,
            "experiment_title": exp.title if exp else "Unknown",
            "status": run.status,
            "overall_score": run.overall_score,
            "duration_seconds": run.duration_seconds,
            "started_at": run.started_at.isoformat() if run.started_at else "",
            "completed_at": run.completed_at.isoformat() if run.completed_at else "",
            "agent_count": len(logs),
            "completed_agents": [l.agent_name for l in logs if l.status == "COMPLETED"],
            "failed_agents": [l.agent_name for l in logs if l.status == "FAILED"],
        })

    return results


@router.get("/runs/{run_id}")
def get_agent_run_status(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed status of a specific analysis run with per-agent logs."""
    run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")

    exp = db.query(Experiment).filter(Experiment.id == run.experiment_id).first()
    if exp and exp.user_id and exp.user_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="You do not have permission to view this analysis run")

    logs = db.query(AgentLog).filter(AgentLog.analysis_run_id == run.id, ~AgentLog.agent_name.like("MCP:%")).order_by(AgentLog.created_at.asc()).all()

    return {
        "run_id": run.id,
        "experiment_id": run.experiment_id,
        "experiment_title": exp.title if exp else "Unknown",
        "status": run.status,
        "overall_score": run.overall_score,
        "duration_seconds": run.duration_seconds,
        "error_message": run.error_message,
        "started_at": run.started_at.isoformat() if run.started_at else "",
        "completed_at": run.completed_at.isoformat() if run.completed_at else "",
        "agents": [
            {
                "agent_name": l.agent_name,
                "status": l.status,
                "execution_time_seconds": l.execution_time_seconds,
                "summary": l.summary,
                "error_message": l.error_message,
                "created_at": l.created_at.isoformat() if l.created_at else "",
                "completed_at": l.completed_at.isoformat() if l.completed_at else "",
            }
            for l in logs
        ]
    }
