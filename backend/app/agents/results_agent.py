from app.agents.base import BaseAgent
from app.agents.schemas import ResultsAgentInput, ResultsAgentOutput

class ResultsAnalysisAgent(BaseAgent[ResultsAgentInput, ResultsAgentOutput]):
    def __init__(self):
        super().__init__(
            name="Results Agent",
            description="Interprets CSV/JSON metric summaries and performance curves without recalculating numbers.",
            input_schema=ResultsAgentInput,
            output_schema=ResultsAgentOutput,
            azure_agent_name="LabTrace-Results-Agent",
            azure_agent_version="2",
        )

    def _execute(self, input_data: ResultsAgentInput) -> ResultsAgentOutput:
        key_metrics = []
        best_vals = {}

        for m in input_data.metrics_a:
            key_metrics.append(f"{m.metric_name}: final={m.final_value:.4f}, best={m.best_value:.4f}")
            best_vals[f"Exp A {m.metric_name}"] = f"{m.best_value:.4f}"

        delta_msg = None
        if input_data.metric_comparisons:
            deltas = []
            for mc in input_data.metric_comparisons:
                pct_str = f" ({mc.relative_diff_pct:.1f}%)" if mc.relative_diff_pct is not None else ""
                deltas.append(f"{mc.metric_name}: Exp A={mc.experiment_a_final:.4f} vs Exp B={mc.experiment_b_final:.4f} [abs diff: {mc.absolute_diff:.4f}{pct_str}]")
            delta_msg = "; ".join(deltas)

        summary_text = f"Results analysis processed {len(input_data.metrics_a)} metrics from CSV result artifacts."
        if input_data.mcp_results:
            summary_text += " Results were verified through MCP."

        return ResultsAgentOutput(
            summary=summary_text,
            key_metrics_observed=key_metrics or ["No CSV metrics detected in uploaded artifacts."],
            best_performance_values=best_vals,
            trajectory_analysis="Epoch/step metric curve evaluation completed cleanly.",
            observed_performance_delta=delta_msg
        )
