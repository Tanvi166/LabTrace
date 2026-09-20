from abc import ABC, abstractmethod
from typing import Any
import time
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.agent_log import AgentLog
from app.models.user import User
from app.services.mcp_tool_service import invoke_tool
class ToolProvider(ABC):
    @abstractmethod
    def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]: ...
class LocalToolProvider(ToolProvider):
    def __init__(self, db: Session, user: User): self.db, self.user = db, user
    def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]: return invoke_tool(name, arguments, self.db, self.user)
class MCPToolProvider(LocalToolProvider):
    """Transport-neutral boundary; HTTP/Foundry clients can replace this later."""


class WorkflowMCPToolProvider(LocalToolProvider):
    """Invoke existing MCP tools and persist workflow-scoped call records."""

    def __init__(self, db: Session, user: User, analysis_run_id: str, experiment_id: str, agent_name: str):
        super().__init__(db, user)
        self.analysis_run_id = analysis_run_id
        self.experiment_id = experiment_id
        self.agent_name = agent_name

    def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        started = time.time()
        log = AgentLog(
            analysis_run_id=self.analysis_run_id,
            agent_name=f"MCP: {self.agent_name}",
            status="RUNNING",
            created_at=datetime.now(timezone.utc),
            structured_output={
                "log_type": "mcp_call",
                "experiment_id": self.experiment_id,
                "agent_name": self.agent_name,
                "tool_name": name,
                "request_summary": arguments,
            },
        )
        self.db.add(log)
        self.db.commit()
        try:
            result = super().call(name, arguments)
            log.status = "COMPLETED"
            log.summary = f"{name} completed"
            log.structured_output = {
                **log.structured_output,
                "response_summary": self._summary(result),
                "success": True,
            }
            return result
        except Exception as exc:
            log.status = "FAILED"
            log.error_message = str(exc)
            log.summary = f"{name} failed"
            log.structured_output = {**log.structured_output, "success": False, "error": str(exc)}
            raise
        finally:
            log.execution_time_seconds = round(time.time() - started, 2)
            log.completed_at = datetime.now(timezone.utc)
            self.db.commit()

    @staticmethod
    def _summary(result: dict[str, Any]) -> dict[str, Any]:
        return {key: (len(value) if isinstance(value, list) else value) for key, value in result.items() if key not in {"content", "findings"}}
