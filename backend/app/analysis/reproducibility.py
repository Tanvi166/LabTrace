import uuid
from typing import List, Dict, Any
from app.analysis.models import (
    ExtractedMetadata,
    ReproducibilityEvaluation,
    ReproducibilityCategoryScore,
    ReproducibilityFinding
)

class ReproducibilityEvaluatorService:
    @staticmethod
    def evaluate(metadata: ExtractedMetadata, filenames: List[str], experiment_desc: str = "") -> ReproducibilityEvaluation:
        findings: List[ReproducibilityFinding] = []
        cat_scores: List[ReproducibilityCategoryScore] = []

        # -------------------------------------------------------------
        # Category 1: Randomness & Seeds (Weight: 25%)
        # -------------------------------------------------------------
        rand_passed = 0
        rand_total = 2
        
        has_seeds = len(metadata.seeds) > 0
        if has_seeds:
            rand_passed += 1
            seed_calls_str = ", ".join([f"{s.library}: {s.call}({s.value or ''})" for s in metadata.seeds])
            findings.append(ReproducibilityFinding(
                id="RAND-01",
                category="randomness",
                severity="HIGH",
                status="PASSED",
                title="Random Seed Configuration",
                evidence=f"Detected random seed calls: {seed_calls_str}",
                recommendation="Maintain deterministic random seeds across all libraries."
            ))
        else:
            findings.append(ReproducibilityFinding(
                id="RAND-01",
                category="randomness",
                severity="HIGH",
                status="FAILED",
                title="Missing Random Seed Configuration",
                evidence="No random seed calls (torch.manual_seed, np.random.seed, etc.) detected in code.",
                recommendation="Configure explicit seeds for Python, NumPy, and PyTorch/TensorFlow."
            ))

        has_cuda_det = any("deterministic" in f for f in metadata.cuda_flags)
        if has_cuda_det:
            rand_passed += 1
            findings.append(ReproducibilityFinding(
                id="RAND-02",
                category="randomness",
                severity="MEDIUM",
                status="PASSED",
                title="Deterministic CUDA Flags",
                evidence=f"CUDA flags configured: {', '.join(metadata.cuda_flags)}",
                recommendation="Ensure CUDA operations remain fully deterministic."
            ))
        else:
            findings.append(ReproducibilityFinding(
                id="RAND-02",
                category="randomness",
                severity="MEDIUM",
                status="WARNING",
                title="Non-Deterministic GPU Execution",
                evidence="No explicit CUDA deterministic flags (e.g., torch.use_deterministic_algorithms) found.",
                recommendation="Set torch.use_deterministic_algorithms(True) to prevent CUDA variance."
            ))

        rand_score = (rand_passed / rand_total) * 100.0
        cat_scores.append(ReproducibilityCategoryScore(
            category="randomness", weight=0.25, score=rand_score, passed_checks=rand_passed, total_checks=rand_total
        ))

        # -------------------------------------------------------------
        # Category 2: Dependencies & Version Pinning (Weight: 20%)
        # -------------------------------------------------------------
        dep_passed = 0
        dep_total = 2

        has_dep_file = len(metadata.dependencies) > 0
        if has_dep_file:
            dep_passed += 1
            findings.append(ReproducibilityFinding(
                id="DEP-01",
                category="dependencies",
                severity="HIGH",
                status="PASSED",
                title="Dependency Manifest File Present",
                evidence=f"Dependency manifest detected with {len(metadata.dependencies)} package entries.",
                recommendation="Keep dependency lockfile updated."
            ))

            pinned = [pkg for pkg, ver in metadata.dependencies.items() if ver != 'unpinned']
            if len(pinned) > 0 and len(pinned) >= len(metadata.dependencies) * 0.5:
                dep_passed += 1
                findings.append(ReproducibilityFinding(
                    id="DEP-02",
                    category="dependencies",
                    severity="HIGH",
                    status="PASSED",
                    title="Strict Dependency Version Pinning",
                    evidence=f"{len(pinned)} out of {len(metadata.dependencies)} packages are pinned to exact versions.",
                    recommendation="Ensure all dependencies use exact '==' pins."
                ))
            else:
                findings.append(ReproducibilityFinding(
                    id="DEP-02",
                    category="dependencies",
                    severity="HIGH",
                    status="WARNING",
                    title="Unpinned Dependency Versions",
                    evidence="Dependencies contain unpinned packages without exact version constraints.",
                    recommendation="Pin all requirements in requirements.txt with exact versions (e.g. torch==2.1.0)."
                ))
        else:
            findings.append(ReproducibilityFinding(
                id="DEP-01",
                category="dependencies",
                severity="HIGH",
                status="FAILED",
                title="Missing Dependency Lockfile",
                evidence="No requirements.txt, environment.yml, or pyproject.toml found in experiment artifacts.",
                recommendation="Include a requirements.txt or environment.yml file."
            ))
            findings.append(ReproducibilityFinding(
                id="DEP-02",
                category="dependencies",
                severity="HIGH",
                status="FAILED",
                title="Unpinned Environment Dependencies",
                evidence="Cannot verify dependency versions.",
                recommendation="Create a pinned requirements.txt file."
            ))

        dep_score = (dep_passed / dep_total) * 100.0
        cat_scores.append(ReproducibilityCategoryScore(
            category="dependencies", weight=0.20, score=dep_score, passed_checks=dep_passed, total_checks=dep_total
        ))

        # -------------------------------------------------------------
        # Category 3: Environment Specifications (Weight: 15%)
        # -------------------------------------------------------------
        env_passed = 0
        env_total = 2

        if len(metadata.frameworks) > 0:
            env_passed += 1
            findings.append(ReproducibilityFinding(
                id="ENV-01",
                category="environment",
                severity="MEDIUM",
                status="PASSED",
                title="ML Framework Specification",
                evidence=f"Identified ML Framework(s): {', '.join(metadata.frameworks)}",
                recommendation="Document framework major and minor versions."
            ))
        else:
            findings.append(ReproducibilityFinding(
                id="ENV-01",
                category="environment",
                severity="MEDIUM",
                status="WARNING",
                title="Unidentified ML Framework",
                evidence="No standard ML framework (PyTorch, TensorFlow, etc.) imports detected.",
                recommendation="Specify deep learning framework requirements explicitly."
            ))

        if metadata.python_version:
            env_passed += 1
            findings.append(ReproducibilityFinding(
                id="ENV-02",
                category="environment",
                severity="LOW",
                status="PASSED",
                title="Python Runtime Version Specified",
                evidence=f"Python version specified: {metadata.python_version}",
                recommendation="Document exact runtime environment."
            ))
        else:
            findings.append(ReproducibilityFinding(
                id="ENV-02",
                category="environment",
                severity="LOW",
                status="WARNING",
                title="Python Runtime Version Unspecified",
                evidence="No Python version declaration found in environment configuration.",
                recommendation="Specify Python runtime version in environment.yml or README."
            ))

        env_score = (env_passed / env_total) * 100.0
        cat_scores.append(ReproducibilityCategoryScore(
            category="environment", weight=0.15, score=env_score, passed_checks=env_passed, total_checks=env_total
        ))

        # -------------------------------------------------------------
        # Category 4: Dataset Identification (Weight: 15%)
        # -------------------------------------------------------------
        ds_passed = 0
        ds_total = 1

        dataset_name = metadata.hyperparameters.dataset_name
        has_ds_file = any("dataset" in f.lower() or "data" in f.lower() for f in filenames)
        if dataset_name or has_ds_file:
            ds_passed += 1
            findings.append(ReproducibilityFinding(
                id="DATA-01",
                category="dataset",
                severity="HIGH",
                status="PASSED",
                title="Dataset Metadata Present",
                evidence=f"Dataset identified: '{dataset_name or 'Artifact dataset files detected'}'",
                recommendation="Include dataset SHA-256 hash or version link."
            ))
        else:
            findings.append(ReproducibilityFinding(
                id="DATA-01",
                category="dataset",
                severity="HIGH",
                status="WARNING",
                title="Missing Dataset Reference",
                evidence="No dataset metadata or dataset name found in code/configs.",
                recommendation="Document dataset name, version, and download link in README or config.yaml."
            ))

        ds_score = (ds_passed / ds_total) * 100.0
        cat_scores.append(ReproducibilityCategoryScore(
            category="dataset", weight=0.15, score=ds_score, passed_checks=ds_passed, total_checks=ds_total
        ))

        # -------------------------------------------------------------
        # Category 5: Configuration Completeness (Weight: 15%)
        # -------------------------------------------------------------
        cfg_passed = 0
        cfg_total = 2

        params = metadata.hyperparameters
        specified_count = sum(1 for p in [params.learning_rate, params.batch_size, params.epochs, params.optimizer] if p is not None)
        if specified_count >= 2:
            cfg_passed += 1
            findings.append(ReproducibilityFinding(
                id="CFG-01",
                category="configuration",
                severity="MEDIUM",
                status="PASSED",
                title="Hyperparameter Specification",
                evidence=f"Specified hyperparameters: lr={params.learning_rate}, batch_size={params.batch_size}, epochs={params.epochs}, optimizer={params.optimizer}",
                recommendation="Store all training parameters in a central config.yaml file."
            ))
        else:
            findings.append(ReproducibilityFinding(
                id="CFG-01",
                category="configuration",
                severity="MEDIUM",
                status="WARNING",
                title="Incomplete Hyperparameter Specification",
                evidence="Key hyperparameters (learning rate, batch size, optimizer) are not explicitly declared.",
                recommendation="Define hyperparameters in config.yaml or script arguments."
            ))

        if len(params.raw_params) > 0:
            cfg_passed += 1
            findings.append(ReproducibilityFinding(
                id="CFG-02",
                category="configuration",
                severity="LOW",
                status="PASSED",
                title="External Config File Used",
                evidence=f"Detected {len(params.raw_params)} parameter key-value pairs in configuration files.",
                recommendation="Keep configuration decoupled from executable code."
            ))
        else:
            findings.append(ReproducibilityFinding(
                id="CFG-02",
                category="configuration",
                severity="LOW",
                status="WARNING",
                title="Hardcoded Configuration Values",
                evidence="No standalone JSON/YAML/TOML configuration file found.",
                recommendation="Export hardcoded parameters into a config.yaml file."
            ))

        cfg_score = (cfg_passed / cfg_total) * 100.0
        cat_scores.append(ReproducibilityCategoryScore(
            category="configuration", weight=0.15, score=cfg_score, passed_checks=cfg_passed, total_checks=cfg_total
        ))

        # -------------------------------------------------------------
        # Category 6: Documentation & Instructions (Weight: 10%)
        # -------------------------------------------------------------
        doc_passed = 0
        doc_total = 1

        has_readme = any("readme" in f.lower() for f in filenames) or len(experiment_desc) > 10
        if has_readme:
            doc_passed += 1
            findings.append(ReproducibilityFinding(
                id="DOC-01",
                category="documentation",
                severity="MEDIUM",
                status="PASSED",
                title="Experiment Documentation Present",
                evidence="README file or experiment documentation found in artifacts.",
                recommendation="Include explicit step-by-step reproduction command instructions."
            ))
        else:
            findings.append(ReproducibilityFinding(
                id="DOC-01",
                category="documentation",
                severity="MEDIUM",
                status="WARNING",
                title="Missing README / Reproduction Instructions",
                evidence="No README.md file or detailed description provided.",
                recommendation="Create a README.md documenting setup and execution instructions."
            ))

        doc_score = (doc_passed / doc_total) * 100.0
        cat_scores.append(ReproducibilityCategoryScore(
            category="documentation", weight=0.10, score=doc_score, passed_checks=doc_passed, total_checks=doc_total
        ))

        # Calculate Overall Weighted Score (0.0 - 100.0)
        overall = sum(cs.score * cs.weight for cs in cat_scores)

        return ReproducibilityEvaluation(
            overall_score=round(overall, 1),
            category_scores=cat_scores,
            findings=findings
        )
