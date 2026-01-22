"""Get all information about JavaScript technologies."""

from pathlib import Path
from app.scanners.technologies.base import TecnologyScanner


class JavaScriptScanner(TecnologyScanner):
    def __init__(self, repo_path: Path) -> None:
        self._repo_path = repo_path

    def scan(self) -> dict | None:
        """Scan Javascript and Typescript languages."""
        js_files = []
        ts_files = []
        
        for file_path in self._repo_path.rglob("*"):
            if file_path.suffix == ".js":
                js_files.append(str(file_path))
            elif file_path.suffix in {".ts",}:
                ts_files.append(str(file_path))

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
        }
