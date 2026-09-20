from app.analysis.code_analyzer import CodeAnalyzerService

def test_codebase_diffing():
    files_a = {
        "main.py": b"def train():\n    print('Epoch 1')\n\ndef eval():\n    pass",
        "old_helper.py": b"def help(): pass"
    }

    files_b = {
        "main.py": b"def train():\n    print('Epoch 1 modified')\n\ndef eval():\n    pass\n\ndef new_func():\n    pass",
        "new_module.py": b"class Model: pass"
    }

    diffs = CodeAnalyzerService.compare_codebases(files_a, files_b)
    diff_map = {d.filename: d for d in diffs}

    assert diff_map["old_helper.py"].change_type == "removed"
    assert diff_map["new_module.py"].change_type == "added"
    assert diff_map["main.py"].change_type == "modified"

    ast_diffs = diff_map["main.py"].ast_function_diffs
    assert any(f.name == "new_func" and f.change_type == "added" for f in ast_diffs)
    assert any(f.name == "train" and f.change_type == "modified" for f in ast_diffs)
