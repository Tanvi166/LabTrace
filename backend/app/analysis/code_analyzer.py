import ast
import difflib
from typing import Dict, List
from app.analysis.models import CodeFileDiff, CodeFunctionDiff

def get_ast_functions(code_str: str) -> Dict[str, str]:
    funcs = {}
    try:
        tree = ast.parse(code_str)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                funcs[node.name] = ast.unparse(node)
    except Exception:
        pass
    return funcs

class CodeAnalyzerService:
    @staticmethod
    def compare_codebases(
        files_a: Dict[str, bytes],
        files_b: Dict[str, bytes]
    ) -> List[CodeFileDiff]:
        all_filenames = sorted(list(set(files_a.keys()).union(set(files_b.keys()))))
        diffs: List[CodeFileDiff] = []

        for fname in all_filenames:
            content_a = files_a.get(fname)
            content_b = files_b.get(fname)

            if content_a is not None and content_b is None:
                diffs.append(CodeFileDiff(
                    filename=fname,
                    change_type="removed",
                    text_diff_lines=[f"- File '{fname}' removed in Experiment B"]
                ))
            elif content_a is None and content_b is not None:
                diffs.append(CodeFileDiff(
                    filename=fname,
                    change_type="added",
                    text_diff_lines=[f"+ File '{fname}' added in Experiment B"]
                ))
            else:
                str_a = content_a.decode('utf-8', errors='ignore') if content_a else ""
                str_b = content_b.decode('utf-8', errors='ignore') if content_b else ""

                if str_a == str_b:
                    diffs.append(CodeFileDiff(
                        filename=fname,
                        change_type="unchanged",
                        text_diff_lines=[]
                    ))
                else:
                    # Text unified diff
                    text_diff = list(difflib.unified_diff(
                        str_a.splitlines(),
                        str_b.splitlines(),
                        fromfile=f"a/{fname}",
                        tofile=f"b/{fname}",
                        lineterm=""
                    ))

                    # AST function diff for Python files
                    ast_func_diffs: List[CodeFunctionDiff] = []
                    if fname.endswith('.py'):
                        funcs_a = get_ast_functions(str_a)
                        funcs_b = get_ast_functions(str_b)

                        all_funcs = set(funcs_a.keys()).union(set(funcs_b.keys()))
                        for f_name in all_funcs:
                            body_a = funcs_a.get(f_name)
                            body_b = funcs_b.get(f_name)

                            if body_a and not body_b:
                                ast_func_diffs.append(CodeFunctionDiff(name=f_name, file=fname, change_type="removed"))
                            elif not body_a and body_b:
                                ast_func_diffs.append(CodeFunctionDiff(name=f_name, file=fname, change_type="added"))
                            elif body_a != body_b:
                                ast_func_diffs.append(CodeFunctionDiff(name=f_name, file=fname, change_type="modified"))

                    diffs.append(CodeFileDiff(
                        filename=fname,
                        change_type="modified",
                        text_diff_lines=text_diff,
                        ast_function_diffs=ast_func_diffs
                    ))

        return diffs
