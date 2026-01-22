from abc import ABC, abstractmethod
from pathlib import Path


class TecnologyScanner(ABC):
    def __init__(self, repo_path: Path) -> None:
        self._repo_path = repo_path

    @abstractmethod
    def scan(self) -> dict | None:
        """Scan lenguage-specific technologies in the repository."""
        pass
