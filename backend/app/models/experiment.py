import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, Float, ForeignKey, JSON, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base

class Experiment(Base):
    __tablename__ = "experiments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="CREATED", nullable=False)  # CREATED, UPLOADING, READY, ANALYZING, COMPLETED, FAILED
    tags = Column(JSON, default=list)  # list of strings
    
    # Metadata summary
    framework = Column(String(100), nullable=True)
    python_version = Column(String(50), nullable=True)
    reproducibility_score = Column(Float, nullable=True)  # 0.0 - 100.0
    
    # Owner
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    files = relationship("ExperimentFile", back_populates="experiment", cascade="all, delete-orphan")
    analysis_runs = relationship("AnalysisRun", back_populates="experiment", cascade="all, delete-orphan")
    experiment_runs = relationship("ExperimentRun", back_populates="experiment", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="experiment", cascade="all, delete-orphan")


class ExperimentFile(Base):
    __tablename__ = "experiment_files"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id = Column(String(36), ForeignKey("experiments.id"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    safe_filename = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)  # display filename
    file_type = Column(String(50), nullable=False)  # code, config, metric, log, dataset_meta, env, archive, other
    content_type = Column(String(100), nullable=True)
    file_extension = Column(String(20), nullable=True)
    storage_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    sha256_hash = Column(String(64), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    experiment = relationship("Experiment", back_populates="files")


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id = Column(String(36), ForeignKey("experiments.id"), nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, RUNNING, COMPLETED, FAILED
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    overall_score = Column(Float, nullable=True)
    extracted_metadata = Column(JSON, nullable=True)
    findings = Column(JSON, default=list)  # list of finding dicts
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    experiment = relationship("Experiment", back_populates="analysis_runs")
    agent_logs = relationship("AgentLog", back_populates="analysis_run", cascade="all, delete-orphan")


class ExperimentRun(Base):
    """Structured run metadata; artifacts continue to reside in Blob Storage."""

    __tablename__ = "experiment_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id = Column(String(36), ForeignKey("experiments.id"), nullable=False, index=True)
    run_id = Column(String(100), nullable=False, index=True)
    status = Column(String(50), default="PENDING", nullable=False)
    model_name = Column(String(255), nullable=True)
    dataset_version = Column(String(255), nullable=True)
    random_seed = Column(Integer, nullable=True)
    metrics = Column(JSON, default=dict)
    result_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    experiment = relationship("Experiment", back_populates="experiment_runs")
