from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.agent_log import AgentLog
from app.models.experiment import AnalysisRun, Experiment
from app.services.mcp_tool_service import TOOL_DEFINITIONS, invoke_tool

router = APIRouter()

recent_calls: list[dict] = []
class ToolInvocation(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    arguments: dict = Field(default_factory=dict)

@router.get("/status")
def mcp_status(current_user: User = Depends(get_current_user)):
    return {
        "status": "ready",
        "transport": "authenticated HTTP tool bridge",
        "external_mcp_server": "available when optional mcp package is installed",
        "tools_count": len(TOOL_DEFINITIONS)
    }

@router.get("/tools")
def list_mcp_tools(current_user: User = Depends(get_current_user)): return {"tools": TOOL_DEFINITIONS}

@router.get("/calls")
def get_recent_calls(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = (
        db.query(AgentLog)
        .join(AnalysisRun, AgentLog.analysis_run_id == AnalysisRun.id)
        .join(Experiment, AnalysisRun.experiment_id == Experiment.id)
        .filter(AgentLog.agent_name.like("MCP:%"))
    )
    if current_user.role != "ADMIN":
        query = query.filter(Experiment.user_id == current_user.id)
    workflow_calls = []
    for log in query.order_by(AgentLog.created_at.desc()).limit(50).all():
        details = log.structured_output or {}
        workflow_calls.append({
            "name": details.get("tool_name"),
            "status": log.status,
            "analysis_run_id": log.analysis_run_id,
            "experiment_id": details.get("experiment_id"),
            "agent_name": details.get("agent_name"),
            "request_summary": details.get("request_summary"),
            "response_summary": details.get("response_summary"),
            "error": log.error_message,
            "duration_seconds": log.execution_time_seconds,
            "timestamp": log.created_at.isoformat() if log.created_at else "",
        })
    manual_calls = [item for item in recent_calls if item["user_id"] == current_user.id or current_user.role == "ADMIN"]
    return {"calls": [*workflow_calls, *manual_calls][:50]}

@router.post("/tools/call")
def call_tool(request: ToolInvocation, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        result = invoke_tool(request.name, request.arguments, db, current_user)
        recent_calls.append({"name": request.name, "user_id": current_user.id, "status": "COMPLETED"})
        del recent_calls[:-50]
        return {"result": result}
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc))
    except PermissionError as exc: raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc))
