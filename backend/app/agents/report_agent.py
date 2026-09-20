from typing import List, Dict, Any
from app.agents.base import BaseAgent
from app.agents.schemas import (
    MetadataAgentOutput,
    CodeAgentOutput,
    ResultsAgentOutput,
    ReproducibilityAgentOutput,
    StructuredReportOutput,
    ReportFindingItem
)
from app.agents.schemas import KnowledgeAgentOutput
from pydantic import BaseModel

class ReportAgentInput(BaseModel):
    experiment_a_title: str
    experiment_b_title: str = ""
    metadata_out: MetadataAgentOutput
    code_out: CodeAgentOutput
    results_out: ResultsAgentOutput
    reproducibility_out: ReproducibilityAgentOutput
    knowledge_out: KnowledgeAgentOutput | None = None

class ReportAgent(BaseAgent[ReportAgentInput, StructuredReportOutput]):
    def __init__(self):
        super().__init__(
            name="Report Agent",
            description="Synthesizes structured Markdown, HTML, and JSON audit reports.",
            input_schema=ReportAgentInput,
            output_schema=StructuredReportOutput
        )

    def _execute(self, input_data: ReportAgentInput) -> StructuredReportOutput:
        title = f"Reproducibility Audit Report — {input_data.experiment_a_title}"
        if input_data.experiment_b_title:
            title = f"Comparative Reproducibility Audit — {input_data.experiment_a_title} vs {input_data.experiment_b_title}"

        exec_summary = (
            f"Reproducibility Assessment Score: {input_data.reproducibility_out.overall_score}/100. "
            f"The experiment framework was identified as {input_data.metadata_out.detected_environment}. "
            f"{input_data.code_out.summary} {input_data.results_out.summary}"
        )

        overview = f"Analyzed artifacts for experiment '{input_data.experiment_a_title}'."
        if input_data.experiment_b_title:
            overview += f" Compared with variant experiment '{input_data.experiment_b_title}'."

        env_analysis = f"{input_data.metadata_out.summary} Missing Metadata: {', '.join(input_data.metadata_out.missing_metadata) if input_data.metadata_out.missing_metadata else 'None'}."
        code_diff_analysis = input_data.code_out.interpretation
        results_analysis = f"{input_data.results_out.summary} {input_data.results_out.observed_performance_delta or ''}"
        repro_assessment = input_data.reproducibility_out.summary

        # Findings are copied from the deterministic evaluator; agents only explain them.
        findings_items = input_data.reproducibility_out.findings

        recs = input_data.reproducibility_out.actionable_recommendations
        evidence_sources = input_data.metadata_out.evidence_notes + input_data.results_out.key_metrics_observed
        external = input_data.knowledge_out.evidence if input_data.knowledge_out else []
        evidence_sources += [f"External guidance: {item.title} ({item.source}, chunk {item.chunk_id})" for item in external]

        # Generate Markdown Content
        md = f"""# {title}

## Executive Summary
{exec_summary}

## 1. Experiment Overview
{overview}

## 2. Environment & Dependencies
{env_analysis}

## 3. Code & Configuration Analysis
{code_diff_analysis}

## 4. Results & Metric Analysis
{results_analysis}

## 5. Reproducibility Score & Audit Assessment
**Overall Reproducibility Score**: `{input_data.reproducibility_out.overall_score}/100`

### Key Recommendations
"""
        for r in recs:
            md += f"- {r}\n"
        md += "\n## Evidence boundaries\n### Observed Experiment Evidence\n"
        md += "\n".join(f"- {item}" for item in input_data.metadata_out.evidence_notes + input_data.results_out.key_metrics_observed)
        md += "\n### External Knowledge\n" + ("\n".join(f"- {item.title} — {item.source} (chunk {item.chunk_id}): {item.content}" for item in external) or "- No matching local guidance was retrieved.")
        md += "\n### AI Interpretation\nThe recommendations interpret the deterministic evidence and the explicitly listed external guidance.\n"

        # Generate HTML Content
        html = f"""
        <div style="font-family: sans-serif; padding: 20px; color: #1e293b;">
          <h1 style="color: #0f172a;">{title}</h1>
          <div style="background-color: #f1f5f9; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #1e40af;">Executive Summary</h3>
            <p>{exec_summary}</p>
            <p><strong>Reproducibility Score:</strong> <span style="font-size: 1.2em; font-weight: bold; color: #059669;">{input_data.reproducibility_out.overall_score}/100</span></p>
          </div>
          <h2>1. Experiment Overview</h2>
          <p>{overview}</p>
          <h2>2. Environment & Codebase Analysis</h2>
          <p>{env_analysis}</p>
          <p>{code_diff_analysis}</p>
          <h2>3. Results & Metric Trajectories</h2>
          <p>{results_analysis}</p>
        </div>
        """

        return StructuredReportOutput(
            title=title,
            executive_summary=exec_summary,
            experiment_overview=overview,
            environment_analysis=env_analysis,
            code_and_config_differences=code_diff_analysis,
            results_and_metric_analysis=results_analysis,
            reproducibility_assessment=repro_assessment,
            overall_score=input_data.reproducibility_out.overall_score,
            findings=findings_items,
            actionable_recommendations=recs,
            evidence_sources=evidence_sources,
            markdown_content=md,
            html_content=html
        )
