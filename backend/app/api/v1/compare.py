from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.experiment import Experiment
from app.api.v1.deps import get_current_user
from app.services.storage_service import get_storage_provider
from app.analysis import ExperimentComparisonService

router = APIRouter()

class ComparisonRequest(BaseModel):
    experiment_a_id: str
    experiment_b_id: str

@router.post("")
def compare_experiments(
    req: ComparisonRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if req.experiment_a_id == req.experiment_b_id:
        raise HTTPException(status_code=400, detail="Cannot compare an experiment with itself. Please select two different experiments.")

    # Validate ownership of both experiments
    exp_a = db.query(Experiment).filter(Experiment.id == req.experiment_a_id).first()
    exp_b = db.query(Experiment).filter(Experiment.id == req.experiment_b_id).first()

    if not exp_a or not exp_b:
        raise HTTPException(status_code=404, detail="One or both experiments were not found.")

    if current_user.role != "ADMIN":
        if (exp_a.user_id and exp_a.user_id != current_user.id) or (exp_b.user_id and exp_b.user_id != current_user.id):
            raise HTTPException(status_code=403, detail="You do not have permission to compare these experiments.")

    storage = get_storage_provider()

    # Download files for Experiment A
    files_a = {}
    for f in exp_a.files:
        if storage.file_exists(f.storage_path):
            files_a[f.filename] = storage.download_file(f.storage_path)

    # Download files for Experiment B
    files_b = {}
    for f in exp_b.files:
        if storage.file_exists(f.storage_path):
            files_b[f.filename] = storage.download_file(f.storage_path)

    comparison_res = ExperimentComparisonService.compare_experiments(
        exp_a_id=exp_a.id,
        exp_a_title=exp_a.title,
        exp_a_desc=exp_a.description or "",
        files_a=files_a,
        exp_b_id=exp_b.id,
        exp_b_title=exp_b.title,
        exp_b_desc=exp_b.description or "",
        files_b=files_b
    )

    return comparison_res.model_dump()


@router.post("/ai")
def ai_compare_experiments(
    req: ComparisonRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run the full multi-agent AI comparison workflow between two experiments.
    
    Invokes all 6 agents using deterministic Phase 3 outputs and produces
    a structured report with agent logs persisted to the database.
    """
    from app.agents.workflow import AgentWorkflowEngine

    if req.experiment_a_id == req.experiment_b_id:
        raise HTTPException(status_code=400, detail="Cannot compare an experiment with itself.")

    exp_a = db.query(Experiment).filter(Experiment.id == req.experiment_a_id).first()
    exp_b = db.query(Experiment).filter(Experiment.id == req.experiment_b_id).first()

    if not exp_a or not exp_b:
        raise HTTPException(status_code=404, detail="One or both experiments were not found.")

    if current_user.role != "ADMIN":
        if (exp_a.user_id and exp_a.user_id != current_user.id) or (exp_b.user_id and exp_b.user_id != current_user.id):
            raise HTTPException(status_code=403, detail="You do not have permission to compare these experiments.")

    try:
        result = AgentWorkflowEngine.run_workflow(
            experiment_id=exp_a.id,
            compare_with_experiment_id=exp_b.id,
            db=db,
            current_user=current_user,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI comparison failed: {str(e)}")
