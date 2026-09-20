from app.agents.base import BaseAgent
from app.agents.schemas import CoordinatorInput, CoordinatorOutput

class CoordinatorAgent(BaseAgent[CoordinatorInput, CoordinatorOutput]):
    def __init__(self):
        super().__init__(
            name="Coordinator Agent",
            description="Orchestrates multi-agent execution pipeline DAG and task sequencing.",
            input_schema=CoordinatorInput,
            output_schema=CoordinatorOutput
        )

    def _execute(self, input_data: CoordinatorInput) -> CoordinatorOutput:
        dag = [
            "Coordinator Agent",
            "Metadata Agent",
            "Code Analysis Agent",
            "Results Agent",
            "Reproducibility Agent",
            "Knowledge Agent",
            "Report Agent"
        ]
        mode_str = "Comparison Evaluation" if input_data.mode == "compare" else "Single Experiment Audit"
        return CoordinatorOutput(
            workflow_dag=dag,
            dependencies={
                "Metadata Agent": ["Coordinator Agent"],
                "Code Analysis Agent": ["Metadata Agent"],
                "Results Agent": ["Code Analysis Agent"],
                "Reproducibility Agent": ["Results Agent"],
                "Knowledge Agent": ["Reproducibility Agent"],
                "Report Agent": ["Knowledge Agent"],
            },
            mode=input_data.mode,
            status="SUCCESS",
            summary=f"Constructed DAG with 7 specialized agents for {mode_str}."
        )
