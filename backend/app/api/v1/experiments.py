import os
import mimetypes
import io
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.experiment import Experiment, ExperimentFile, ExperimentRun
from app.api.v1.deps import get_current_user
from app.services.storage_service import get_storage_provider
from app.services.zip_service import ZipSecurityExtractor, determine_file_type

router = APIRouter()

ALLOWED_EXTENSIONS = {
    '.py', '.ipynb', '.csv', '.tsv', '.json', '.yaml', '.yml', '.toml',
    '.txt', '.md', '.log', '.sh', '.r', '.zip'
}
ALLOWED_BASE_NAMES = {'requirements.txt', 'environment.yml', 'pyproject.toml', 'readme.md'}
MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # 100 MB

# Pydantic Schemas
class ExperimentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    tags: List[str] = []

class ExperimentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class FileItemResponse(BaseModel):
    id: str
    original_filename: str
    safe_filename: str
    filename: str
    file_type: str
    content_type: Optional[str] = None
    file_extension: Optional[str] = None
    file_size_bytes: int
    created_at: str

class ExperimentResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: str
    tags: List[str]
    framework: Optional[str] = None
    python_version: Optional[str] = None
    reproducibility_score: Optional[float] = None
    created_at: str
    updated_at: str
    files_count: int = 0
    files: List[FileItemResponse] = []

class ExperimentPaginatedList(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[ExperimentResponse]

class FileContentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    content_type: str
    file_size_bytes: int
    content: Optional[str] = None
    is_binary: bool = False
    is_truncated: bool = False


class ExperimentRunCreate(BaseModel):
    run_id: Optional[str] = Field(default=None, min_length=1, max_length=100)
    status: str = Field(default="PENDING", min_length=1, max_length=50)
    model_name: Optional[str] = Field(default=None, max_length=255)
    dataset_version: Optional[str] = Field(default=None, max_length=255)
    random_seed: Optional[int] = Field(default=None, ge=0)
    metrics: dict = Field(default_factory=dict)
    result_metadata: dict = Field(default_factory=dict)


class ExperimentRunResponse(BaseModel):
    id: str
    experiment_id: str
    run_id: str
    status: str
    model_name: Optional[str] = None
    dataset_version: Optional[str] = None
    random_seed: Optional[int] = None
    metrics: dict
    result_metadata: dict
    created_at: str
    updated_at: str

# Helpers
def verify_experiment_access(experiment_id: str, current_user: User, db: Session) -> Experiment:
    exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if exp.user_id and exp.user_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="You do not have permission to access this experiment")
    return exp

def serialize_experiment(exp: Experiment) -> ExperimentResponse:
    files_list = []
    for f in (exp.files or []):
        files_list.append(FileItemResponse(
            id=f.id,
            original_filename=f.original_filename,
            safe_filename=f.safe_filename,
            filename=f.filename,
            file_type=f.file_type,
            content_type=f.content_type,
            file_extension=f.file_extension,
            file_size_bytes=f.file_size_bytes,
            created_at=f.created_at.isoformat() if f.created_at else ""
        ))
    return ExperimentResponse(
        id=exp.id,
        title=exp.title,
        description=exp.description,
        status=exp.status or "CREATED",
        tags=exp.tags or [],
        framework=exp.framework,
        python_version=exp.python_version,
        reproducibility_score=exp.reproducibility_score,
        created_at=exp.created_at.isoformat() if exp.created_at else "",
        updated_at=exp.updated_at.isoformat() if exp.updated_at else "",
        files_count=len(files_list),
        files=files_list
    )


def serialize_experiment_run(run: ExperimentRun) -> ExperimentRunResponse:
    return ExperimentRunResponse(
        id=run.id,
        experiment_id=run.experiment_id,
        run_id=run.run_id,
        status=run.status,
        model_name=run.model_name,
        dataset_version=run.dataset_version,
        random_seed=run.random_seed,
        metrics=run.metrics or {},
        result_metadata=run.result_metadata or {},
        created_at=run.created_at.isoformat() if run.created_at else "",
        updated_at=run.updated_at.isoformat() if run.updated_at else "",
    )

# Routes
@router.post("", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
def create_experiment(
    data: ExperimentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    exp = Experiment(
        title=data.title,
        description=data.description,
        tags=data.tags,
        status="CREATED",
        user_id=current_user.id
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return serialize_experiment(exp)

@router.get("", response_model=ExperimentPaginatedList)
def list_experiments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Experiment)
    if current_user.role != "ADMIN":
        query = query.filter(Experiment.user_id == current_user.id)
    
    if search:
        pattern = f"%{search}%"
        query = query.filter(Experiment.title.ilike(pattern) | Experiment.description.ilike(pattern))
        
    total = query.count()
    items = query.order_by(Experiment.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return ExperimentPaginatedList(
        total=total,
        page=page,
        page_size=page_size,
        items=[serialize_experiment(exp) for exp in items]
    )

@router.get("/{experiment_id}", response_model=ExperimentResponse)
def get_experiment(
    experiment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    exp = verify_experiment_access(experiment_id, current_user, db)
    return serialize_experiment(exp)


@router.post("/{experiment_id}/runs", response_model=ExperimentRunResponse, status_code=status.HTTP_201_CREATED)
def create_experiment_run(
    experiment_id: str,
    data: ExperimentRunCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exp = verify_experiment_access(experiment_id, current_user, db)
    run = ExperimentRun(
        experiment_id=exp.id,
        run_id=data.run_id or str(uuid.uuid4()),
        status=data.status,
        model_name=data.model_name,
        dataset_version=data.dataset_version,
        random_seed=data.random_seed,
        metrics=data.metrics,
        result_metadata=data.result_metadata,
    )
    try:
        db.add(run)
        db.commit()
        db.refresh(run)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database request failed")
    return serialize_experiment_run(run)


@router.get("/{experiment_id}/runs", response_model=List[ExperimentRunResponse])
def list_experiment_runs(
    experiment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exp = verify_experiment_access(experiment_id, current_user, db)
    try:
        runs = (
            db.query(ExperimentRun)
            .filter(ExperimentRun.experiment_id == exp.id)
            .order_by(ExperimentRun.created_at.desc())
            .all()
        )
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database request failed")
    return [serialize_experiment_run(run) for run in runs]

@router.patch("/{experiment_id}", response_model=ExperimentResponse)
def update_experiment(
    experiment_id: str,
    data: ExperimentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    exp = verify_experiment_access(experiment_id, current_user, db)
    if data.title is not None:
        exp.title = data.title
    if data.description is not None:
        exp.description = data.description
    if data.tags is not None:
        exp.tags = data.tags
    db.commit()
    db.refresh(exp)
    return serialize_experiment(exp)

@router.delete("/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_experiment(
    experiment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    exp = verify_experiment_access(experiment_id, current_user, db)
    storage = get_storage_provider()
    
    # Delete storage directory/files
    for f in exp.files:
        storage.delete_file(f.storage_path)
        
    db.delete(exp)
    db.commit()
    return None

# File Management Endpoints
@router.post("/{experiment_id}/files", response_model=List[FileItemResponse])
async def upload_experiment_files(
    experiment_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    exp = verify_experiment_access(experiment_id, current_user, db)
    storage = get_storage_provider()
    created_records = []
    
    for upload in files:
        raw_name = upload.filename or "uploaded_file"
        ext = os.path.splitext(raw_name)[1].lower()
        base_name = raw_name.lower()
        
        # Extension validation
        if ext not in ALLOWED_EXTENSIONS and base_name not in ALLOWED_BASE_NAMES:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file type '{ext}' for file '{raw_name}'."
            )
        
        contents = await upload.read()
        if len(contents) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File '{raw_name}' exceeds maximum upload size of {MAX_UPLOAD_BYTES // (1024*1024)} MB."
            )
        
        # Handle ZIP Archives safely
        if ext == '.zip':
            try:
                extracted_meta = ZipSecurityExtractor.inspect_and_extract(contents, exp.id, storage)
                for item in extracted_meta:
                    f_record = ExperimentFile(
                        experiment_id=exp.id,
                        original_filename=item["original_filename"],
                        safe_filename=item["safe_filename"],
                        filename=item["filename"],
                        file_type=item["file_type"],
                        content_type=item["content_type"],
                        file_extension=item["file_extension"],
                        storage_path=item["storage_path"],
                        file_size_bytes=item["file_size_bytes"]
                    )
                    db.add(f_record)
                    db.commit()
                    db.refresh(f_record)
                    created_records.append(f_record)
            except ValueError as ve:
                raise HTTPException(status_code=400, detail=str(ve))
        else:
            # Regular single file upload
            safe_filename = storage._sanitize_filename(raw_name) if hasattr(storage, '_sanitize_filename') else raw_name
            storage_path = storage.upload_file(exp.id, safe_filename, io.BytesIO(contents))
            mime_type, _ = mimetypes.guess_type(raw_name)
            file_type = determine_file_type(raw_name)
            
            f_record = ExperimentFile(
                experiment_id=exp.id,
                original_filename=raw_name,
                safe_filename=safe_filename,
                filename=raw_name,
                file_type=file_type,
                content_type=mime_type or "text/plain",
                file_extension=ext,
                storage_path=storage_path,
                file_size_bytes=len(contents)
            )
            db.add(f_record)
            db.commit()
            db.refresh(f_record)
            created_records.append(f_record)
            
    # Update experiment status to READY if files are attached
    if exp.files:
        exp.status = "READY"
        db.commit()
        
    return [
        FileItemResponse(
            id=f.id,
            original_filename=f.original_filename,
            safe_filename=f.safe_filename,
            filename=f.filename,
            file_type=f.file_type,
            content_type=f.content_type,
            file_extension=f.file_extension,
            file_size_bytes=f.file_size_bytes,
            created_at=f.created_at.isoformat() if f.created_at else ""
        ) for f in created_records
    ]

@router.get("/{experiment_id}/files", response_model=List[FileItemResponse])
def list_experiment_files(
    experiment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    exp = verify_experiment_access(experiment_id, current_user, db)
    return [
        FileItemResponse(
            id=f.id,
            original_filename=f.original_filename,
            safe_filename=f.safe_filename,
            filename=f.filename,
            file_type=f.file_type,
            content_type=f.content_type,
            file_extension=f.file_extension,
            file_size_bytes=f.file_size_bytes,
            created_at=f.created_at.isoformat() if f.created_at else ""
        ) for f in exp.files
    ]

@router.get("/{experiment_id}/files/{file_id}", response_model=FileContentResponse)
def get_file_content(
    experiment_id: str,
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    exp = verify_experiment_access(experiment_id, current_user, db)
    f_record = db.query(ExperimentFile).filter(
        ExperimentFile.id == file_id,
        ExperimentFile.experiment_id == exp.id
    ).first()
    
    if not f_record:
        raise HTTPException(status_code=404, detail="File not found")
        
    storage = get_storage_provider()
    if not storage.file_exists(f_record.storage_path):
        raise HTTPException(status_code=404, detail="File content missing from storage")
        
    raw_bytes = storage.download_file(f_record.storage_path)
    
    # Try decoding text
    is_binary = False
    content_str = None
    is_truncated = False
    
    try:
        text = raw_bytes.decode('utf-8')
        # Check size truncation (max 300KB or 3000 lines)
        max_chars = 300 * 1024
        if len(text) > max_chars:
            text = text[:max_chars]
            is_truncated = True
        content_str = text
    except UnicodeDecodeError:
        is_binary = True
        content_str = "[Binary File - Preview Unavailable]"
        
    return FileContentResponse(
        id=f_record.id,
        filename=f_record.filename,
        file_type=f_record.file_type,
        content_type=f_record.content_type or "text/plain",
        file_size_bytes=f_record.file_size_bytes,
        content=content_str,
        is_binary=is_binary,
        is_truncated=is_truncated
    )

@router.delete("/{experiment_id}/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_experiment_file(
    experiment_id: str,
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    exp = verify_experiment_access(experiment_id, current_user, db)
    f_record = db.query(ExperimentFile).filter(
        ExperimentFile.id == file_id,
        ExperimentFile.experiment_id == exp.id
    ).first()
    
    if not f_record:
        raise HTTPException(status_code=404, detail="File not found")
        
    storage = get_storage_provider()
    storage.delete_file(f_record.storage_path)
    
    db.delete(f_record)
    db.commit()
    return None

# Deterministic Experiment Analysis Endpoint
@router.post("/{experiment_id}/analyze")
def analyze_experiment(
    experiment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    import time
    from datetime import datetime, timezone
    from app.models.experiment import AnalysisRun
    from app.analysis import MetadataExtractorService, ResultsAnalyzerService, ReproducibilityEvaluatorService
    
    exp = verify_experiment_access(experiment_id, current_user, db)
    storage = get_storage_provider()
    
    start_time = time.time()
    run = AnalysisRun(
        experiment_id=exp.id,
        status="RUNNING",
        started_at=datetime.now(timezone.utc)
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    
    try:
        # Load all experiment files from storage
        files_map: dict = {}
        file_names: list = []
        for f in exp.files:
            file_names.append(f.filename)
            if storage.file_exists(f.storage_path):
                files_map[f.filename] = storage.download_file(f.storage_path)
                
        # 1. Deterministic Metadata Extraction
        metadata = MetadataExtractorService.extract_from_files(files_map)
        
        # 2. Results & Metrics Processing
        metric_summaries = ResultsAnalyzerService.analyze_metrics(files_map)
        
        # 3. Deterministic Reproducibility Evaluation
        repro = ReproducibilityEvaluatorService.evaluate(metadata, file_names, exp.description or "")
        
        duration = round(time.time() - start_time, 2)
        
        # Update Experiment entity
        exp.reproducibility_score = repro.overall_score
        exp.framework = ", ".join(metadata.frameworks) if metadata.frameworks else "Generic Python"
        exp.python_version = metadata.python_version or "3.10"
        exp.status = "COMPLETED"
        
        # Update AnalysisRun entity
        run.status = "COMPLETED"
        run.completed_at = datetime.now(timezone.utc)
        run.duration_seconds = duration
        run.overall_score = repro.overall_score
        run.extracted_metadata = metadata.model_dump()
        run.findings = [f.model_dump() for f in repro.findings]
        
        db.commit()
        db.refresh(exp)
        
        return {
            "experiment_id": exp.id,
            "status": "COMPLETED",
            "duration_seconds": duration,
            "overall_score": repro.overall_score,
            "extracted_metadata": metadata.model_dump(),
            "reproducibility": repro.model_dump(),
            "metrics_summary": [m.model_dump() for m in metric_summaries]
        }
        
    except Exception as e:
        run.status = "FAILED"
        run.error_message = str(e)
        exp.status = "FAILED"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# AI-Powered Multi-Agent Analysis Endpoint (Phase 4)
@router.post("/{experiment_id}/ai-analyze")
def ai_analyze_experiment(
    experiment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run the full multi-agent AI analysis workflow on an experiment.
    
    This invokes all 6 agents (Coordinator, Metadata, Code, Results,
    Reproducibility, Report) and persists agent logs and a structured report.
    """
    from app.agents.workflow import AgentWorkflowEngine

    exp = verify_experiment_access(experiment_id, current_user, db)
    
    if not exp.files:
        raise HTTPException(status_code=400, detail="Experiment has no uploaded files. Upload artifacts before running AI analysis.")
    
    exp.status = "ANALYZING"
    db.commit()
    
    try:
        result = AgentWorkflowEngine.run_workflow(
            experiment_id=exp.id,
            compare_with_experiment_id=None,
            db=db,
            current_user=current_user,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")
