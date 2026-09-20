from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.experiment import Experiment
from app.models.report import Report
from app.api.v1.deps import get_current_user

router = APIRouter()


@router.get("")
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all reports accessible to the current user."""
    if current_user.role == "ADMIN":
        reports = db.query(Report).order_by(Report.created_at.desc()).all()
    else:
        reports = (
            db.query(Report)
            .join(Experiment, Report.experiment_id == Experiment.id)
            .filter(Experiment.user_id == current_user.id)
            .order_by(Report.created_at.desc())
            .all()
        )

    return [
        {
            "id": r.id,
            "experiment_id": r.experiment_id,
            "experiment_title": r.experiment.title if r.experiment else "Unknown experiment",
            "analysis_run_id": r.analysis_run_id,
            "title": r.title,
            "summary": r.summary,
            "overall_score": r.structured_json.get("overall_score") if r.structured_json else None,
            "created_at": r.created_at.isoformat() if r.created_at else ""
        }
        for r in reports
    ]


@router.get("/{report_id}")
def get_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific report with full markdown/HTML/JSON content."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Ownership check
    exp = db.query(Experiment).filter(Experiment.id == report.experiment_id).first()
    if exp and exp.user_id and exp.user_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="You do not have permission to view this report")

    return {
        "id": report.id,
        "experiment_id": report.experiment_id,
        "experiment_title": exp.title if exp else "Unknown experiment",
        "analysis_run_id": report.analysis_run_id,
        "title": report.title,
        "summary": report.summary,
        "content_markdown": report.content_markdown,
        "content_html": report.content_html,
        "structured_json": report.structured_json,
        "created_at": report.created_at.isoformat() if report.created_at else ""
    }
