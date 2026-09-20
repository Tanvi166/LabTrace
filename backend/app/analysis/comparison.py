from typing import Dict, List
from app.analysis.models import ComparisonResult
from app.analysis.metadata_extractor import MetadataExtractorService
from app.analysis.code_analyzer import CodeAnalyzerService
from app.analysis.config_diff import ConfigDiffService
from app.analysis.results_analyzer import ResultsAnalyzerService
from app.analysis.reproducibility import ReproducibilityEvaluatorService

class ExperimentComparisonService:
    @staticmethod
    def compare_experiments(
        exp_a_id: str,
        exp_a_title: str,
        exp_a_desc: str,
        files_a: Dict[str, bytes],
        exp_b_id: str,
        exp_b_title: str,
        exp_b_desc: str,
        files_b: Dict[str, bytes]
    ) -> ComparisonResult:
        # Extract metadata
        meta_a = MetadataExtractorService.extract_from_files(files_a)
        meta_b = MetadataExtractorService.extract_from_files(files_b)

        # Code AST & file diffs
        code_diffs = CodeAnalyzerService.compare_codebases(files_a, files_b)

        # Config diffs
        config_diffs = ConfigDiffService.compare_configs(
            meta_a.hyperparameters.raw_params,
            meta_b.hyperparameters.raw_params
        )

        # Dependency diffs
        dep_diffs = ConfigDiffService.compare_dependencies(
            meta_a.dependencies,
            meta_b.dependencies
        )

        # Metric trajectory comparisons
        metrics_a = ResultsAnalyzerService.analyze_metrics(files_a)
        metrics_b = ResultsAnalyzerService.analyze_metrics(files_b)
        metric_comparisons = ResultsAnalyzerService.compare_metrics(metrics_a, metrics_b)

        # Reproducibility evaluation
        repro_a = ReproducibilityEvaluatorService.evaluate(meta_a, list(files_a.keys()), exp_a_desc)
        repro_b = ReproducibilityEvaluatorService.evaluate(meta_b, list(files_b.keys()), exp_b_desc)

        repro_delta = {
            "experiment_a_score": repro_a.overall_score,
            "experiment_b_score": repro_b.overall_score,
            "score_diff": round(repro_b.overall_score - repro_a.overall_score, 1),
            "findings_a_count": len(repro_a.findings),
            "findings_b_count": len(repro_b.findings)
        }

        return ComparisonResult(
            experiment_a_id=exp_a_id,
            experiment_b_id=exp_b_id,
            experiment_a_title=exp_a_title,
            experiment_b_title=exp_b_title,
            code_file_diffs=code_diffs,
            config_diffs=config_diffs,
            dependency_diffs=dep_diffs,
            metric_comparisons=metric_comparisons,
            reproducibility_delta=repro_delta
        )
