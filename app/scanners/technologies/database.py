"""Get all information about Database files."""

from pathlib import Path
from app.core.logger import get_logger
from app.scanners.technologies.base import TecnologyScanner
from app.scanners.technologies.metadata.database_config import (
    BINARY_DB_EXTENSIONS,
    SCRIPT_DB_EXTENSIONS,
    CONFIG_FILES,
    DB_DIRECTORIES,
)

logger = get_logger(__name__)


class DatabaseScanner(TecnologyScanner):
    def __init__(self, repo_path: Path) -> None:
        super().__init__(repo_path)

    def _iter_repo_files(self):
        """Yield repository files, skipping common ignored directories."""
        for file_path in self._repo_path.rglob("*"):
            # Skip common ignore dirs to speed up and avoid noise
            parts = file_path.parts
            if any(
                p in parts
                for p in [
                    "node_modules",
                    "venv",
                    ".venv",
                    "__pycache__",
                    ".git",
                    "site-packages",
                ]
            ):
                continue
            yield file_path

    def scan(self) -> dict | None:
        """Scan for database files."""
        logger.info("Starting Database files scan in %s", self._repo_path)

        binary_dbs = []
        sql_scripts = []
        configs = []
        db_dirs = set()

        for file_path in self._iter_repo_files():
            if not file_path.is_file():
                continue

            if file_path.suffix.lower() in BINARY_DB_EXTENSIONS:
                binary_dbs.append(str(file_path))
                continue

            if file_path.suffix.lower() in SCRIPT_DB_EXTENSIONS:
                sql_scripts.append(str(file_path))
                # Don't continue, check directories too

            if file_path.name in CONFIG_FILES:
                configs.append(str(file_path))
                # Configs can also be in special dirs, so we don't 'continue' here safely if we want to check dir
                # But typically configs are configs. Let's just remove the 'continue' from previous blocks if we want to check dir
                # actually, a file is distinct from the dir check.
                # If a file matches script, it is a script.
                # BUT it also "lives" in a DB dir.
                # So we should check dir for ALL files, not just 'continue' ones.

            # Check if file resides in a known DB directory
            # We look at the parent directory name
            if file_path.parent.name in DB_DIRECTORIES:
                db_dirs.add(str(file_path.parent))

        if not binary_dbs and not sql_scripts and not configs and not db_dirs:
            logger.debug("No database files found.")
            return None

        result = {
            "type": "infrastructure",
            "name": "database",
            "binary_files": {
                "detected": bool(binary_dbs),
                "files": binary_dbs,
                "count": len(binary_dbs),
            },
            "scripts": {
                "detected": bool(sql_scripts),
                "files": sql_scripts,
                "count": len(sql_scripts),
            },
            "configs": {
                "detected": bool(configs),
                "files": configs,
                "count": len(configs),
            },
            "directories": {
                "detected": bool(db_dirs),
                "paths": sorted(db_dirs),
                "count": len(db_dirs),
            },
        }

        logger.info("Database scan finished.")
        return result
