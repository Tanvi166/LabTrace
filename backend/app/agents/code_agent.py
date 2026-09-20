from app.agents.base import BaseAgent
from app.agents.schemas import CodeAgentInput, CodeAgentOutput

class CodeAnalysisAgent(BaseAgent[CodeAgentInput, CodeAgentOutput]):
    def __init__(self):
        super().__init__(
            name="Code Analysis Agent",
            description="Interprets AST function modifications, file changes, and parameter deltas.",
            input_schema=CodeAgentInput,
            output_schema=CodeAgentOutput
        )

    def _execute(self, input_data: CodeAgentInput) -> CodeAgentOutput:
        code_changes = []
        ast_funcs = []
        cfg_changes = []
        dep_changes = []

        for f in input_data.file_diffs:
            if f.change_type != "unchanged":
                code_changes.append(f"File '{f.filename}' status: {f.change_type}")
                for ast_f in f.ast_function_diffs:
                    ast_funcs.append(f"Function '{ast_f.name}()' in {ast_f.file} was {ast_f.change_type}")

        for cfg in input_data.config_diffs:
            if cfg.change_type != "unchanged":
                cfg_changes.append(f"Parameter '{cfg.parameter}': {cfg.experiment_a} -> {cfg.experiment_b} ({cfg.change_type})")

        for dep in input_data.dependency_diffs:
            if dep.change_type != "unchanged":
                dep_changes.append(f"Package '{dep.package}': {dep.version_a} -> {dep.version_b} ({dep.change_type})")

        interpretation_msg = (
            f"Observed {len(code_changes)} file modifications and {len(ast_funcs)} AST function changes. "
            "These configuration and AST changes represent structural pipeline variations between runs."
        )
        if input_data.mcp_files:
            interpretation_msg += f" MCP inspected {len(input_data.mcp_files.get('files', []))} experiment files."

        return CodeAgentOutput(
            summary=f"Codebase analysis complete: {len(code_changes)} file diffs, {len(cfg_changes)} hyperparameter changes.",
            observed_code_changes=code_changes or ["No file structural changes detected."],
            ast_function_modifications=ast_funcs or ["No AST function definition changes detected."],
            configuration_changes=cfg_changes or ["Configuration parameters identical."],
            dependency_changes=dep_changes or ["Dependencies identical."],
            interpretation=interpretation_msg
        )
