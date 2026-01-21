import shutil
import tempfile
from pathlib import Path
from uuid import uuid4


class Workspace:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or Path(tempfile.gettempdir()) / "ira-docgen"
        self.id = uuid4().hex
        self.path = self.base_dir / self.id
        self.repo_path = self.path / "repo"

    def create(self) -> None:
        self.repo_path.mkdir(parents=True, exist_ok=False)

    def cleanup(self) -> None:
        if self.path.exists():
            shutil.rmtree(self.path, ignore_errors=True)
