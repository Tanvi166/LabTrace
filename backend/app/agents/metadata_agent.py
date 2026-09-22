from app.agents.base import BaseAgent
from app.agents.schemas import MetadataAgentInput, MetadataAgentOutput


class MetadataAgent(
    BaseAgent[MetadataAgentInput, MetadataAgentOutput]
):
    def __init__(self):
        super().__init__(
            
            name="Metadata Agent",
            description=(
                "Analyzes environment, frameworks, dependencies, "
                "hardware, and experiment metadata for reproducibility."
            ),
            input_schema=MetadataAgentInput,
            output_schema=MetadataAgentOutput,
            azure_agent_name="LabTrace-Metadata-Agent",
            azure_agent_version="2",
        )

    def _execute(
        self,
        input_data: MetadataAgentInput,
    ) -> MetadataAgentOutput:

        metadata_a = input_data.metadata_a
        metadata_b = input_data.metadata_b

        prompt = f"""
Analyze the metadata of a machine learning experiment.

Experiment A metadata:
{metadata_a.model_dump()}

Experiment B metadata:
{metadata_b.model_dump() if metadata_b else "No Experiment B provided."}

Additional MCP metadata:
{input_data.mcp_metadata}

Analyze:

1. Dataset details
2. Python version and environment
3. Frameworks and libraries
4. Dependencies
5. Hardware / CUDA information
6. Model configuration and hyperparameters
7. Random seed configuration
8. Missing metadata
9. Important differences between Experiment A and B
10. Potential reproducibility implications

Do not invent information.

Only use evidence present in the supplied metadata.

Return a structured metadata analysis.
"""

        system_prompt = """
You are the LabTrace Metadata Agent.

Your job is to analyze machine-learning experiment metadata.

Use only the supplied evidence.
Do not invent datasets, versions, hardware,
dependencies, hyperparameters, or experiment facts.

Identify missing information explicitly.

Return concise, technically accurate structured output.
"""

        return self.provider.generate_structured(
            prompt=prompt,
            schema=MetadataAgentOutput,
            system_prompt=system_prompt,
        )