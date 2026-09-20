import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id = Column(String(36), ForeignKey("experiments.id"), nullable=False)
    analysis_run_id = Column(String(36), ForeignKey("analysis_runs.id"), nullable=True)
    
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    content_markdown = Column(Text, nullable=False)
    content_html = Column(Text, nullable=True)
    structured_json = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    experiment = relationship("Experiment", back_populates="reports")
