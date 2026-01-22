"""Get all information about JavaScript technologies."""

import json
from pathlib import Path

from app.scanners.technologies.base import TecnologyScanner
from app.scanners.technologies.javascript_frameworks import (
    FRAMEWORK_DEPENDENCIES,
    FRAMEWORK_CONFIGS,
)


class JavaScriptScanner(TecnologyScanner):
    def __init__(self, repo_path: Path) -> None:
        self._repo_path = repo_path

    def _iter_repo_files(self):
        """Yield repository files, skipping node_modules."""
        for file_path in self._repo_path.rglob("*"):
            if "node_modules" in file_path.parts:
                continue
            yield file_path

    def _detect_language_files(
        self, file_path: Path, js_files: list[str], ts_files: list[str]
    ) -> bool:
        """Collect JS/TS files and return True if handled."""
        if file_path.suffix == ".js":
            js_files.append(str(file_path))
            return True
        if file_path.suffix == ".ts":
            ts_files.append(str(file_path))
            return True
        return False

    def _detect_frameworks_from_package_json(
        self, file_path: Path, frameworks: set[str]
    ) -> None:
        """Collect frameworks from dependencies in package.json."""
        if file_path.name != "package.json":
            return

        try:
            package_data = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            package_data = {}

        dependencies = package_data.get("dependencies", {})
        dev_dependencies = package_data.get("devDependencies", {})
        package_names = set(dependencies) | set(dev_dependencies)

        for framework, packages in FRAMEWORK_DEPENDENCIES.items():
            if package_names & packages:
                frameworks.add(framework)

    def _detect_frameworks_from_config(
        self, file_path: Path, frameworks: set[str]
    ) -> None:
        """Collect frameworks from known config files."""
        if not file_path.is_file():
            return

        for framework, config_files in FRAMEWORK_CONFIGS.items():
            if file_path.name in config_files:
                frameworks.add(framework)

    def scan(self) -> dict | None:
        """Scan Javascript and Typescript languages."""
        js_files = []
        ts_files = []
        frameworks = set()

        for file_path in self._iter_repo_files():
            if self._detect_language_files(file_path, js_files, ts_files):
                continue
            self._detect_frameworks_from_package_json(file_path, frameworks)
            self._detect_frameworks_from_config(file_path, frameworks)

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
