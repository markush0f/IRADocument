"""Get all information about JavaScript technologies."""

import json
from pathlib import Path

from app.scanners.technologies.base import TecnologyScanner
from app.scanners.technologies.javascript_frameworks import (
    FRAMEWORK_CONFIGS,
    FRAMEWORK_DEPENDENCIES,
)


class JavaScriptScanner(TecnologyScanner):
    def __init__(self, repo_path: Path) -> None:
        self._repo_path = repo_path

    def scan(self) -> dict | None:
        """Scan Javascript and Typescript languages."""
        js_files = []
        ts_files = []
        frameworks = set()

        framework_dependencies = FRAMEWORK_DEPENDENCIES
        framework_configs = FRAMEWORK_CONFIGS
        
        for file_path in self._repo_path.rglob("*"):
            if "node_modules" in file_path.parts:
                continue

            if file_path.suffix == ".js":
                js_files.append(str(file_path))
            elif file_path.suffix in {".ts",}:
                ts_files.append(str(file_path))
            elif file_path.name == "package.json":
                try:
                    package_data = json.loads(file_path.read_text(encoding="utf-8"))
                except Exception:
                    package_data = {}

                dependencies = package_data.get("dependencies", {})
                dev_dependencies = package_data.get("devDependencies", {})
                package_names = set(dependencies) | set(dev_dependencies)

                for framework, packages in framework_dependencies.items():
                    if package_names & packages:
                        frameworks.add(framework)
            elif file_path.is_file():
                for framework, config_files in framework_configs.items():
                    if file_path.name in config_files:
                        frameworks.add(framework)

        if not js_files and not ts_files:
            return None

        return {
            "language": "javascript/typescript",
            "javascript": {
                "detected": bool(js_files),
                "files": js_files,
                "count": len(js_files),
            },
            "typescript": {
                "detected": bool(ts_files),
                "files": ts_files,
                "count": len(ts_files),
            },
            "frameworks": {
                "detected": bool(frameworks),
                "items": sorted(frameworks),
                "count": len(frameworks),
            },
        }
