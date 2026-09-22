from app.agents.base import BaseAgent
from app.agents.schemas import CodeAgentInput, CodeAgentOutput


class CodeAnalysisAgent(
    BaseAgent[CodeAgentInput, CodeAgentOutput]
):
    def __init__(self):
        super().__init__(
            name="Code Analysis Agent",
            description=(
                "Analyzes and compares implementation code, "
                "configuration, dependencies, and AST changes "
                "between machine learning experiments."
            ),
            input_schema=CodeAgentInput,
            output_schema=CodeAgentOutput,
            azure_agent_name="LabTrace-Code-Agent",
            azure_agent_version="2",
        )

    def _execute(
        self,
        input_data: CodeAgentInput,
    ) -> CodeAgentOutput:

        prompt = f"""
Analyze the implementation and configuration differences
between machine learning experiments.

Code file differences:
{[item.model_dump() for item in input_data.file_diffs]}

Configuration differences:
{[item.model_dump() for item in input_data.config_diffs]}

Dependency differences:
{[item.model_dump() for item in input_data.dependency_diffs]}

Additional experiment files:
{input_data.mcp_files}

Relevant file contents:
{input_data.mcp_file_contents}

Analyze:

1. Code implementation changes
2. Function or AST changes
3. Data loading and preprocessing changes
4. Model architecture changes
5. Training procedure changes
6. Configuration and hyperparameter changes
7. Dependency/version changes
8. Changes that could affect experiment results
9. Changes that could affect reproducibility
10. Missing information

Do not invent code changes or experiment facts.

Only use the supplied evidence.

Return a structured code analysis.
"""

        system_prompt = """
You are the LabTrace Code Analysis Agent.

Analyze machine-learning experiment implementation differences.

Base every conclusion only on the supplied code,
configuration, dependency, and file evidence.

Do not invent files, functions, parameters,
dependencies, or implementation details.

Clearly distinguish observed changes from interpretation.

Return concise, technically accurate structured output.
"""

        return self.provider.generate_structured(
            prompt=prompt,
            schema=CodeAgentOutput,
            system_prompt=system_prompt,
        )