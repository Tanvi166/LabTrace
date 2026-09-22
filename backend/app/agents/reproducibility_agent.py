from app.agents.base import BaseAgent
from app.agents.schemas import (
    ReproducibilityAgentInput,
    ReproducibilityAgentOutput,
)


class ReproducibilityAgent(
    BaseAgent[ReproducibilityAgentInput, ReproducibilityAgentOutput]
):
    def __init__(self):
        super().__init__(
            name="Reproducibility Agent",
            description=(
                "Analyzes deterministic reproducibility findings using "
                "the Azure AI Foundry Reproducibility Agent."
            ),
            input_schema=ReproducibilityAgentInput,
            output_schema=ReproducibilityAgentOutput,
        )

    def _execute(
        self,
        input_data: ReproducibilityAgentInput,
    ) -> ReproducibilityAgentOutput:

        eval_obj = input_data.evaluation

        findings_data = []

        for finding in eval_obj.findings:
            findings_data.append({
                "title": finding.title,
                "category": finding.category,
                "severity": finding.severity,
                "status": finding.status,
                "evidence": finding.evidence,
                "recommendation": finding.recommendation,
            })

        prompt = f"""
Analyze the reproducibility findings for a machine learning experiment.

Deterministic reproducibility score:
{eval_obj.overall_score}/100

Findings:
{findings_data}

Additional MCP findings:
{input_data.mcp_findings}

Return a structured reproducibility assessment.

You must:
1. Explain the reproducibility score.
2. Analyze randomness, dependencies, environment, dataset,
   configuration, and documentation.
3. Identify important reproducibility issues.
4. Give actionable recommendations.
5. Preserve the evidence from the supplied findings.
6. Do not invent experiment facts.
"""

        system_prompt = """
You are the LabTrace Reproducibility Agent.

Your job is to analyze machine-learning experiment reproducibility
using the supplied deterministic findings and evidence.

Do not invent evidence, experiment results, datasets, or configurations.
Base your assessment only on the supplied information.
Return concise, technically accurate structured output.
"""

        return self.provider.generate_structured(
            prompt=prompt,
            schema=ReproducibilityAgentOutput,
            system_prompt=system_prompt,
        )