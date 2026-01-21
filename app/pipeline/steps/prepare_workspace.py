"""Workspace creation step for the pipeline."""

from pathlib import Path
from uuid import uuid4
import tempfile


class WorkspaceError(Exception):
    """Raised when the workspace setup fails."""


def prepare_workspace(context) -> None:
    """Create an isolated workspace directory and attach paths to context."""
    base_tmp = Path(tempfile.gettempdir()) / "ira-docgen"

    workspace_id = uuid4().hex
    workspace_path = base_tmp / workspace_id
    repo_path = workspace_path / "repo"

    try:
        repo_path.mkdir(parents=True, exist_ok=False)
    except Exception as exc:
        raise WorkspaceError(f"Failed to create workspace at {repo_path}") from exc

    context.workspace_id = workspace_id
    context.workspace_path = workspace_path
    context.repo_path = repo_path
