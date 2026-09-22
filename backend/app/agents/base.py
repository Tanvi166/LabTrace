import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Type, TypeVar, Generic, Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.agent_log import AgentLog
from app.agents.providers.azure_provider import get_model_provider


I = TypeVar("I", bound=BaseModel)
O = TypeVar("O", bound=BaseModel)


class BaseAgent(Generic[I, O], ABC):

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: Type[I],
        output_schema: Type[O],
        azure_agent_name: Optional[str] = None,
        azure_agent_version: Optional[str] = None,
    ):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.output_schema = output_schema

        if azure_agent_name:
            self.provider = get_model_provider(
                agent_name=azure_agent_name,
                agent_version=azure_agent_version,
            )
        else:
            self.provider = get_model_provider()

    @abstractmethod
    def _execute(self, input_data: I) -> O:
        """Subclasses implement agent-specific logic consuming deterministic Phase 3 outputs."""
        pass

    def run(
        self,
        input_data: I,
        analysis_run_id: str,
        db: Session
    ) -> O:

        log_entry = AgentLog(
            analysis_run_id=analysis_run_id,
            agent_name=self.name,
            status="RUNNING",
            created_at=datetime.now(timezone.utc)
        )

        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        start_time = time.time()

        try:
            output = self._execute(input_data)

            duration = round(time.time() - start_time, 2)

            log_entry.status = "COMPLETED"
            log_entry.completed_at = datetime.now(timezone.utc)
            log_entry.execution_time_seconds = duration

            log_entry.structured_output = {
                "input_summary": {
                    "input_type": type(input_data).__name__,
                    "fields": list(
                        input_data.model_dump().keys()
                    ),
                },
                "output": output.model_dump(),
            }

            log_entry.summary = getattr(
                output,
                "summary",
                f"{self.name} completed successfully."
            )

            db.commit()

            return output

        except Exception as e:

            duration = round(
                time.time() - start_time,
                2
            )

            log_entry.status = "FAILED"
            log_entry.completed_at = datetime.now(timezone.utc)
            log_entry.execution_time_seconds = duration
            log_entry.error_message = str(e)

            db.commit()

            raise e