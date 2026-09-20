from app.agents.base import BaseAgent
from app.agents.schemas import ReproducibilityAgentInput, ReproducibilityAgentOutput, ReportFindingItem

class ReproducibilityAgent(BaseAgent[ReproducibilityAgentInput, ReproducibilityAgentOutput]):
    def __init__(self):
        super().__init__(
            name="Reproducibility Agent",
            description="Explains deterministic reproducibility score and structures recommendations by severity.",
            input_schema=ReproducibilityAgentInput,
            output_schema=ReproducibilityAgentOutput
        )

    def _execute(self, input_data: ReproducibilityAgentInput) -> ReproducibilityAgentOutput:
        eval_obj = input_data.evaluation
        overall_score = eval_obj.overall_score

        sev_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        recs = []
        report_findings = []

        rand_audit = "Randomness controls missing"
        dep_audit = "Dependency manifest unpinned"
        env_audit = "Environment specified"
        ds_audit = "Dataset referenced"
        cfg_audit = "Config specified"
        doc_audit = "Documentation present"

        for f in eval_obj.findings:
            if f.severity in sev_counts:
                sev_counts[f.severity] += 1
            if f.status != "PASSED":
                recs.append(f"[{f.severity}] {f.recommendation}")

            report_findings.append(ReportFindingItem(
                title=f.title,
                category=f.category,
                severity=f.severity,
                observed_evidence=f.evidence,
                interpretation=(
                    "This assessment is based on the deterministic reproducibility evaluation."
                ),
                recommendation=f.recommendation,
            ))

            if f.category == "randomness":
                rand_audit = f"{f.title}: {f.evidence}"
            elif f.category == "dependencies":
                dep_audit = f"{f.title}: {f.evidence}"
            elif f.category == "environment":
                env_audit = f"{f.title}: {f.evidence}"
            elif f.category == "dataset":
                ds_audit = f"{f.title}: {f.evidence}"
            elif f.category == "configuration":
                cfg_audit = f"{f.title}: {f.evidence}"
            elif f.category == "documentation":
                doc_audit = f"{f.title}: {f.evidence}"

        summary_text = f"Reproducibility score: {overall_score}/100. Evaluated {len(eval_obj.findings)} audit checks."
        if input_data.mcp_findings:
            summary_text += " Findings were verified through MCP."

        return ReproducibilityAgentOutput(
            overall_score=overall_score,
            summary=summary_text,
            randomness_audit=rand_audit,
            dependency_audit=dep_audit,
            environment_audit=env_audit,
            dataset_audit=ds_audit,
            configuration_audit=cfg_audit,
            documentation_audit=doc_audit,
            severity_breakdown=sev_counts,
            actionable_recommendations=recs or ["No failing deterministic reproducibility checks were identified."],
            findings=report_findings,
        )
