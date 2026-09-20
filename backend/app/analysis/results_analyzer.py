import io
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from app.analysis.models import MetricSummary, MetricComparison

METRIC_NAME_PATTERNS = ['acc', 'accuracy', 'loss', 'f1', 'precision', 'recall', 'auc', 'val_loss', 'val_acc', 'reward', 'error']
STEP_PATTERNS = ['epoch', 'step', 'iter', 'iteration']

class ResultsAnalyzerService:
    @staticmethod
    def analyze_metrics(files_content: Dict[str, bytes]) -> List[MetricSummary]:
        summaries: List[MetricSummary] = []

        for filename, content_bytes in files_content.items():
            if not (filename.endswith('.csv') or filename.endswith('.tsv')):
                continue

            try:
                df = pd.read_csv(io.BytesIO(content_bytes))
                if df.empty:
                    continue

                step_col = None
                for col in df.columns:
                    if str(col).lower() in STEP_PATTERNS:
                        step_col = col
                        break

                for col in df.columns:
                    col_lower = str(col).lower()
                    # Skip step columns or non-numeric columns
                    if col == step_col or not pd.api.types.is_numeric_dtype(df[col]):
                        continue

                    # If column matches metric keywords or is numerical
                    if any(pat in col_lower for pat in METRIC_NAME_PATTERNS) or len(df[col]) > 1:
                        series = df[col].dropna()
                        if series.empty:
                            continue

                        vals = series.values
                        best_val = float(np.min(vals)) if 'loss' in col_lower or 'error' in col_lower else float(np.max(vals))

                        trajectory = []
                        for idx, val in enumerate(vals):
                            step_val = int(df[step_col].iloc[idx]) if step_col and idx < len(df[step_col]) else idx + 1
                            trajectory.append({"step": step_val, "value": float(val)})

                        summaries.append(MetricSummary(
                            metric_name=str(col),
                            min_value=float(np.min(vals)),
                            max_value=float(np.max(vals)),
                            mean_value=float(np.mean(vals)),
                            std_value=float(np.std(vals)) if len(vals) > 1 else 0.0,
                            final_value=float(vals[-1]),
                            best_value=best_val,
                            trajectory=trajectory
                        ))
            except Exception:
                continue

        return summaries

    @staticmethod
    def compare_metrics(
        metrics_a: List[MetricSummary],
        metrics_b: List[MetricSummary]
    ) -> List[MetricComparison]:
        comparisons: List[MetricComparison] = []
        map_a = {m.metric_name: m for m in metrics_a}
        map_b = {m.metric_name: m for m in metrics_b}

        common_metrics = set(map_a.keys()).intersection(set(map_b.keys()))

        for name in sorted(list(common_metrics)):
            ma = map_a[name]
            mb = map_b[name]

            abs_diff = abs(ma.final_value - mb.final_value)
            rel_pct = (abs_diff / abs(ma.final_value) * 100.0) if ma.final_value != 0 else None

            # Align trajectory steps for Recharts
            traj_a_map = {pt["step"]: pt["value"] for pt in ma.trajectory}
            traj_b_map = {pt["step"]: pt["value"] for pt in mb.trajectory}
            all_steps = sorted(list(set(traj_a_map.keys()).union(set(traj_b_map.keys()))))

            combined_traj = []
            for s in all_steps:
                combined_traj.append({
                    "step": s,
                    "exp_a": traj_a_map.get(s),
                    "exp_b": traj_b_map.get(s)
                })

            comparisons.append(MetricComparison(
                metric_name=name,
                experiment_a_final=ma.final_value,
                experiment_b_final=mb.final_value,
                experiment_a_best=ma.best_value,
                experiment_b_best=mb.best_value,
                absolute_diff=abs_diff,
                relative_diff_pct=rel_pct,
                combined_trajectory=combined_traj
            ))

        return comparisons
