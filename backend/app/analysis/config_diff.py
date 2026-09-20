from typing import Dict, List
from app.analysis.models import ConfigParamDiff, DependencyDiff

class ConfigDiffService:
    @staticmethod
    def compare_configs(params_a: Dict[str, str], params_b: Dict[str, str]) -> List[ConfigParamDiff]:
        all_keys = sorted(list(set(params_a.keys()).union(set(params_b.keys()))))
        diffs: List[ConfigParamDiff] = []

        for k in all_keys:
            val_a = params_a.get(k)
            val_b = params_b.get(k)

            if val_a is not None and val_b is None:
                diffs.append(ConfigParamDiff(parameter=k, experiment_a=val_a, experiment_b=None, change_type="removed"))
            elif val_a is None and val_b is not None:
                diffs.append(ConfigParamDiff(parameter=k, experiment_a=None, experiment_b=val_b, change_type="added"))
            elif str(val_a) != str(val_b):
                diffs.append(ConfigParamDiff(parameter=k, experiment_a=val_a, experiment_b=val_b, change_type="changed"))
            else:
                diffs.append(ConfigParamDiff(parameter=k, experiment_a=val_a, experiment_b=val_b, change_type="unchanged"))

        return diffs

    @staticmethod
    def compare_dependencies(deps_a: Dict[str, str], deps_b: Dict[str, str]) -> List[DependencyDiff]:
        all_pkgs = sorted(list(set(deps_a.keys()).union(set(deps_b.keys()))))
        diffs: List[DependencyDiff] = []

        for pkg in all_pkgs:
            ver_a = deps_a.get(pkg)
            ver_b = deps_b.get(pkg)

            if ver_a is not None and ver_b is None:
                diffs.append(DependencyDiff(package=pkg, version_a=ver_a, version_b=None, change_type="removed"))
            elif ver_a is None and ver_b is not None:
                diffs.append(DependencyDiff(package=pkg, version_a=None, version_b=ver_b, change_type="added"))
            elif ver_a != ver_b:
                diffs.append(DependencyDiff(package=pkg, version_a=ver_a, version_b=ver_b, change_type="version_changed"))
            else:
                diffs.append(DependencyDiff(package=pkg, version_a=ver_a, version_b=ver_b, change_type="unchanged"))

        return diffs
