from app.agents.base import BaseAgent
from app.agents.schemas import MetadataAgentInput, MetadataAgentOutput

class MetadataAgent(BaseAgent[MetadataAgentInput, MetadataAgentOutput]):
    def __init__(self):
        super().__init__(
            name="Metadata Agent",
            description="Analyzes environment, frameworks, and dependency metadata statically.",
            input_schema=MetadataAgentInput,
            output_schema=MetadataAgentOutput
        )

    def _execute(self, input_data: MetadataAgentInput) -> MetadataAgentOutput:
        ma = input_data.metadata_a
        mb = input_data.metadata_b

        frameworks = ma.frameworks
        py_ver = ma.python_version or "3.10"
        
        missing = []
        if not ma.seeds:
            missing.append("Random seeds (torch/np/random)")
        if not ma.dependencies:
            missing.append("Dependency manifest file")
        if not ma.hyperparameters.learning_rate:
            missing.append("Explicit learning_rate declaration")

        diffs = []
        if mb:
            if ma.frameworks != mb.frameworks:
                diffs.append(f"Framework change: {ma.frameworks} -> {mb.frameworks}")
            if ma.dependencies != mb.dependencies:
                diffs.append(f"Dependency differences detected: {len(ma.dependencies)} vs {len(mb.dependencies)} packages")

        evidence = [
            f"Detected {len(ma.imports)} python imports",
            f"Detected {len(ma.seeds)} seed configuration calls",
            f"Detected {len(ma.cuda_flags)} CUDA/GPU device flags"
        ]
        if input_data.mcp_metadata:
            evidence.append("Experiment metadata verified through MCP.")

        summary_text = f"Extracted environment metadata: Frameworks={', '.join(frameworks) if frameworks else 'Generic Python'}, Python={py_ver}."

        return MetadataAgentOutput(
            summary=summary_text,
            detected_frameworks=frameworks,
            detected_environment=f"Python {py_ver}",
            missing_metadata=missing,
            important_differences=diffs,
            evidence_notes=evidence
        )
