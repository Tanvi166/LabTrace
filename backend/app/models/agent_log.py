import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class AgentLog(Base):
    __tablename__ = "agent_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_run_id = Column(String(36), ForeignKey("analysis_runs.id"), nullable=False)
    
    agent_name = Column(String(100), nullable=False)  # Orchestrator, Metadata, Diff, Reproducibility, RAG, Report
    status = Column(String(50), nullable=False)  # PENDING, RUNNING, COMPLETED, FAILED
    execution_time_seconds = Column(Float, nullable=True)
    
    summary = Column(Text, nullable=True)
    structured_output = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    analysis_run = relationship("AnalysisRun", back_populates="agent_logs")
