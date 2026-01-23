"""Get all information about Docker technologies."""

from pathlib import Path
from app.core.logger import get_logger

from app.scanners.technologies.base import TecnologyScanner
from app.scanners.technologies.metadata.docker_config import (
    DOCKER_COMPOSE_FILES,
    DOCKER_FILES,
    DOCKER_IGNORE_FILES,
)


logger = get_logger(__name__)


class DockerScanner(TecnologyScanner):
    def __init__(self, repo_path: Path) -> None:
        super().__init__(repo_path)

    def _iter_repo_files(self):
        """Yield repository files."""
        for file_path in self._repo_path.rglob("*"):
            yield file_path

    def _is_dockerfile(self, file_path: Path) -> bool:
        """Check if file is a Dockerfile."""
        if file_path.name in DOCKER_FILES:
            return True
        # Handle Dockerfile.ext or .Dockerfile
        if file_path.name.startswith("Dockerfile.") or file_path.name.endswith(
            ".Dockerfile"
        ):
            return True
        return False

    def scan(self) -> dict | None:
        """Scan Docker configuration."""
        dockerfiles_paths = []
        compose_files_paths = []
        ignore_files_paths = []

        for file_path in self._iter_repo_files():
            if not file_path.is_file():
                continue

            if self._is_dockerfile(file_path):
                dockerfiles_paths.append(str(file_path))
                continue

            if file_path.name in DOCKER_COMPOSE_FILES:
                compose_files_paths.append(str(file_path))
                continue

            if file_path.name in DOCKER_IGNORE_FILES:
                ignore_files_paths.append(str(file_path))
                continue

        if not dockerfiles_paths and not compose_files_paths and not ignore_files_paths:
            logger.debug("No Docker configuration files found.")
            return None

        result = {
            "type": "infrastructure",
            "name": "docker",
            "dockerfiles": {
                "detected": bool(dockerfiles_paths),
                "files": dockerfiles_paths,
                "count": len(dockerfiles_paths),
            },
            "compose_files": {
                "detected": bool(compose_files_paths),
                "files": compose_files_paths,
                "count": len(compose_files_paths),
            },
            "ignore_files": {
                "detected": bool(ignore_files_paths),
                "files": ignore_files_paths,
                "count": len(ignore_files_paths),
            },
        }

        logger.info("Docker scan finished.")
        return result
