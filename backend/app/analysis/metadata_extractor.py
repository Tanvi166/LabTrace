import os
import ast
import json
import yaml
import re

from typing import List, Dict, Any, Tuple
from app.analysis.models import ExtractedMetadata, DetectedSeed, ExtractedHyperparameters

class PyASTVisitor(ast.NodeVisitor):
    def __init__(self, filename: str):
        self.filename = filename
        self.imports: List[str] = []
        self.seeds: List[DetectedSeed] = []
        self.cuda_flags: List[str] = []
        self.functions: List[str] = []
        self.classes: List[str] = []
        self.hyperparams: Dict[str, Any] = {}

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            self.imports.append(node.module)
            for alias in node.names:
                self.imports.append(f"{node.module}.{alias.name}")
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.functions.append(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.classes.append(node.name)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Detect seed calls statically
        try:
            call_repr = ast.unparse(node.func)
        except Exception:
            call_repr = ""

        val_str = None
        if node.args:
            try:
                val_str = ast.unparse(node.args[0])
            except Exception:
                val_str = "expression"

        if "np.random.seed" in call_repr or "numpy.random.seed" in call_repr:
            self.seeds.append(DetectedSeed(library="numpy", call=call_repr, value=val_str, file=self.filename))
        elif "random.seed" in call_repr:
            self.seeds.append(DetectedSeed(library="python_random", call=call_repr, value=val_str, file=self.filename))
        elif "torch.cuda.manual_seed" in call_repr or "torch.cuda.manual_seed_all" in call_repr:
            self.seeds.append(DetectedSeed(library="torch_cuda", call=call_repr, value=val_str, file=self.filename))
        elif "torch.manual_seed" in call_repr:
            self.seeds.append(DetectedSeed(library="torch_cpu", call=call_repr, value=val_str, file=self.filename))
        elif "tf.random.set_seed" in call_repr or "set_seed" in call_repr:
            self.seeds.append(DetectedSeed(library="tensorflow", call=call_repr, value=val_str, file=self.filename))


        # Detect CUDA / device flags
        if "torch.device" in call_repr:
            self.cuda_flags.append(f"device_call({val_str or ''})")
        elif "use_deterministic_algorithms" in call_repr:
            self.cuda_flags.append("torch.use_deterministic_algorithms(True)")

        self.generic_visit(node)


    def visit_Assign(self, node: ast.Assign):
        # Detect hyperparameter variable assignments e.g. lr = 0.001, batch_size = 32
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id.lower()
                try:
                    val = ast.literal_eval(node.value)
                    if var_name in ['lr', 'learning_rate', 'batch_size', 'epochs', 'seed', 'optimizer', 'momentum', 'weight_decay']:
                        self.hyperparams[var_name] = val
                except Exception:
                    pass

                if 'cudnn.deterministic' in target.id or 'deterministic' in var_name:
                    self.cuda_flags.append(f"{target.id} set")

        self.generic_visit(node)

    def _get_attribute_name(self, node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            val_name = self._get_attribute_name(node.value)
            return f"{val_name}.{node.attr}" if val_name else node.attr
        return None


class MetadataExtractorService:
    @staticmethod
    def extract_from_files(files_content: Dict[str, bytes]) -> ExtractedMetadata:
        frameworks = set()
        imports_set = set()
        dependencies: Dict[str, str] = {}
        seeds: List[DetectedSeed] = []
        cuda_flags: List[str] = []
        hyperparams_map: Dict[str, Any] = {}
        python_version: Optional[str] = None

        for filename, content_bytes in files_content.items():
            base_lower = os.path.basename(filename).lower()
            ext = os.path.splitext(filename)[1].lower()

            try:
                text_content = content_bytes.decode('utf-8', errors='ignore')
            except Exception:
                continue

            # 1. Python AST parsing
            if ext == '.py':
                try:
                    tree = ast.parse(text_content, filename=filename)
                    visitor = PyASTVisitor(filename)
                    visitor.visit(tree)

                    imports_set.update(visitor.imports)
                    seeds.extend(visitor.seeds)
                    cuda_flags.extend(visitor.cuda_flags)
                    hyperparams_map.update(visitor.hyperparams)
                except Exception:
                    pass

            # 2. Requirements.txt parsing
            elif base_lower == 'requirements.txt':
                for line in text_content.splitlines():
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = re.split(r'==|>=|<=|~=', line)
                        pkg = parts[0].strip().lower()
                        ver = parts[1].strip() if len(parts) > 1 else 'unpinned'
                        dependencies[pkg] = ver

            # 3. YAML & Config parsing (config.yaml, environment.yml)
            elif ext in ['.yaml', '.yml']:
                try:
                    yaml_data = yaml.safe_load(text_content)
                    if isinstance(yaml_data, dict):
                        # Environment file parsing
                        if 'dependencies' in yaml_data:
                            for dep in yaml_data['dependencies']:
                                if isinstance(dep, str):
                                    if 'python' in dep:
                                        python_version = dep.split('=')[-1]
                                    parts = dep.split('=')
                                    dependencies[parts[0]] = parts[1] if len(parts) > 1 else 'unpinned'

                        # Hyperparameters parsing
                        for k, v in yaml_data.items():
                            k_lower = k.lower()
                            if k_lower in ['learning_rate', 'lr', 'batch_size', 'epochs', 'optimizer', 'seed', 'dataset', 'model']:
                                hyperparams_map[k_lower] = v
                except Exception:
                    pass

            # 4. JSON Config parsing
            elif ext == '.json':
                try:
                    json_data = json.loads(text_content)
                    if isinstance(json_data, dict):
                        for k, v in json_data.items():
                            k_lower = k.lower()
                            if k_lower in ['learning_rate', 'lr', 'batch_size', 'epochs', 'optimizer', 'seed', 'dataset', 'model']:
                                hyperparams_map[k_lower] = v
                except Exception:
                    pass

        # Framework detection from imports & dependencies
        all_libs = imports_set.union(set(dependencies.keys()))
        for lib in all_libs:
            lib_lower = lib.lower()
            if 'torch' in lib_lower:
                frameworks.add('PyTorch')
            elif 'tensorflow' in lib_lower or 'keras' in lib_lower:
                frameworks.add('TensorFlow')
            elif 'sklearn' in lib_lower or 'scikit-learn' in lib_lower:
                frameworks.add('scikit-learn')
            elif 'jax' in lib_lower:
                frameworks.add('JAX')

        hyper_obj = ExtractedHyperparameters(
            learning_rate=float(hyperparams_map.get('learning_rate') or hyperparams_map.get('lr') or 0.0) or None,
            batch_size=int(hyperparams_map.get('batch_size') or 0) or None,
            epochs=int(hyperparams_map.get('epochs') or 0) or None,
            optimizer=str(hyperparams_map.get('optimizer')) if hyperparams_map.get('optimizer') else None,
            scheduler=str(hyperparams_map.get('scheduler')) if hyperparams_map.get('scheduler') else None,
            model_name=str(hyperparams_map.get('model')) if hyperparams_map.get('model') else None,
            dataset_name=str(hyperparams_map.get('dataset')) if hyperparams_map.get('dataset') else None,
            raw_params=hyperparams_map
        )

        return ExtractedMetadata(
            frameworks=sorted(list(frameworks)),
            python_version=python_version or '3.10 (Standard)',
            imports=sorted(list(imports_set)),
            dependencies=dependencies,
            seeds=seeds,
            cuda_flags=list(set(cuda_flags)),
            hyperparameters=hyper_obj
        )
