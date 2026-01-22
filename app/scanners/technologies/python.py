"""Get all information about Python technologies."""

from pathlib import Path

try:
    import tomllib
except ImportError:
    tomllib = None

from app.scanners.technologies.base import TecnologyScanner
from app.scanners.technologies.python_frameworks import (
    FRAMEWORK_CONFIGS,
    FRAMEWORK_DEPENDENCIES,
)


class PythonScanner(TecnologyScanner):
    def __init__(self, repo_path: Path) -> None:
        self._repo_path = repo_path

    def _iter_repo_files(self):
        """Yield repository files, skipping venvs and caches."""
        for file_path in self._repo_path.rglob("*"):
            parts = file_path.parts
            if any(
                p in parts
                for p in [
                    "__pycache__",
                    "venv",
                    ".venv",
                    "env",
                    ".env",
                    "site-packages",
                    ".git",
                    ".idea",
                    ".vscode",
                ]
            ):
                continue
            yield file_path

    def _detect_language_files(
        self, file_path: Path, py_files: list[str], ipynb_files: list[str]
    ) -> bool:
        """Collect Python files and return True if handled."""
        if file_path.suffix == ".py":
            py_files.append(str(file_path))
            return True
        if file_path.suffix == ".ipynb":
            ipynb_files.append(str(file_path))
            return True
        return False

    def _detect_frameworks_from_requirements(
        self, file_path: Path, frameworks: set[str]
    ) -> None:
        """Collect frameworks from requirements.txt."""
        if file_path.name != "requirements.txt":
            return

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return

        # Simple parsing of requirements.txt
        # Remove comments and parse lines
        found_packages = set()
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Handle cases like 'package==1.0.0', 'package>=1.0', '-r other.txt'
            if line.startswith("-"):
                continue
            # split by valid version specifiers or just take the first part
            # This is a naive parser but usually sufficient for scanning
            package_name = (
                line.split("==")[0]
                .split(">=")[0]
                .split("<=")[0]
                .split("~=")[0]
                .split("!=")[0]
                .split(">")[0]
                .split("<")[0]
                .split(";")[0]
                .split(" ")[0]
                .strip()
                .lower()
            )
            found_packages.add(package_name)

        for framework, packages in FRAMEWORK_DEPENDENCIES.items():
            if found_packages & packages:
                frameworks.add(framework)

    def _detect_frameworks_from_pyproject(
        self, file_path: Path, frameworks: set[str]
    ) -> None:
        """Collect frameworks from pyproject.toml."""
        if file_path.name != "pyproject.toml":
            return

        if not tomllib:
            return

        try:
            data = tomllib.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            return

        found_packages = set()

        # Check standard locations for dependencies
        # 1. project.dependencies (PEP 621)
        project = data.get("project", {})
        deps = project.get("dependencies", [])
        for dep in deps:
            # Similar parsing to requirements
            if isinstance(dep, str):
                package_name = (
                    dep.split("==")[0]
                    .split(">=")[0]
                    .split("<=")[0]
                    .split("~=")[0]
                    .split("!=")[0]
                    .split(">")[0]
                    .split("<")[0]
                    .split(";")[0]
                    .split(" ")[0]
                    .strip()
                    .lower()
                )
                found_packages.add(package_name)

        # 2. tool.poetry.dependencies
        tool = data.get("tool", {})
        poetry = tool.get("poetry", {})
        poetry_deps = poetry.get("dependencies", {})
        if isinstance(poetry_deps, dict):
            found_packages.update(k.lower() for k in poetry_deps.keys())

        for framework, packages in FRAMEWORK_DEPENDENCIES.items():
            if found_packages & packages:
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
        """Scan Python languages."""
        py_files = []
        ipynb_files = []
        frameworks = set()

        for file_path in self._iter_repo_files():
            self._detect_language_files(file_path, py_files, ipynb_files)
            # We continue even if language file detected, because a .py file implies it's a python project
            # but we also need to check metadata files which are usually files too.
            # But specific metadata files are handled by specific methods.
            self._detect_frameworks_from_requirements(file_path, frameworks)
            self._detect_frameworks_from_pyproject(file_path, frameworks)
            self._detect_frameworks_from_config(file_path, frameworks)

        if not py_files and not ipynb_files:
            return None

        return {
            "language": "python",
            "python": {
                "detected": bool(py_files),
                "files": py_files,
                "count": len(py_files),
            },
            "jupyter": {
                "detected": bool(ipynb_files),
                "files": ipynb_files,
                "count": len(ipynb_files),
            },
            "frameworks": {
                "detected": bool(frameworks),
                "items": sorted(frameworks),
                "count": len(frameworks),
            },
        }
