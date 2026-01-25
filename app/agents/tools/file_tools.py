from typing import List, Dict, Any, Optional
from .registry import registry
from app.services.file_service import FileService
from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger

logger = get_logger(__name__)


@registry.tool
async def list_project_files(project_id: str) -> List[Dict[str, Any]]:
    """Lists all files that have been registered for a project."""
    async with AsyncSessionLocal() as session:
        service = FileService(session)
        files = await service.get_project_files(project_id)
        return [
            {
                "path": f.path,
                "language": f.language,
                "analyzed": bool(f.analyzed),
                "summary": f.summary,
            }
            for f in files
        ]


@registry.tool
async def register_file(
    project_id: str, path: str, language: Optional[str] = None
) -> Dict[str, Any]:
    """Registers a new file in the project database."""
    async with AsyncSessionLocal() as session:
        service = FileService(session)
        file_obj = await service.register_file(project_id, path, language)
        return {"status": "success", "path": file_obj.path}


@registry.tool
async def read_file_content(project_id: str, path: str) -> Dict[str, Any]:
    """
    Reads the full content of a file from the local filesystem.
    This is useful for analyzing configuration files like package.json, requirements.txt, or source code.
    """
    async with AsyncSessionLocal() as session:
        # First get project to get the root_path
        from app.services.project_service import ProjectService

        p_service = ProjectService(session)
        project = await p_service.get_project(project_id)
        if not project:
            return {"error": f"Project {project_id} not found"}

        import os

        full_path = os.path.join(project.root_path, path)

        try:
            if not os.path.exists(full_path):
                return {"error": f"File {path} does not exist at {full_path}"}

            import aiofiles

            async with aiofiles.open(full_path, mode="r", encoding="utf-8") as f:
                content = await f.read()

            return {"path": path, "content": content, "length": len(content)}
        except Exception as e:
            return {"error": f"Could not read file {path}: {str(e)}"}


@registry.tool
async def list_directory_content(project_id: str, path: str = "") -> Dict[str, Any]:
    """
    Lists files and directories at a given path within the project root.
    Use this to explore the project structure.
    """
    async with AsyncSessionLocal() as session:
        from app.services.project_service import ProjectService

        project_service = ProjectService(session)
        project = await project_service.get_project(project_id)
        if not project:
            return {"error": f"Project {project_id} not found"}

        import os

        # Handle cases where the agent might provide an absolute path instead of relative
        if os.path.isabs(path) and path.startswith(project.root_path):
            path = os.path.relpath(path, project.root_path)
            if path == ".":
                path = ""

        full_path = os.path.normpath(os.path.join(project.root_path, path))
        logger.info(f"Listing directory: {full_path} (Root: {project.root_path})")

        # Security check: ensure path is within project root
        if not full_path.startswith(os.path.normpath(project.root_path)):
            return {"error": "Access denied: Path outside project root"}

        try:
            if not os.path.exists(full_path):
                return {"error": f"Path {path} does not exist"}

            items = os.listdir(full_path)
            content = []
            for item in items:
                item_full_path = os.path.join(full_path, item)
                is_dir = os.path.isdir(item_full_path)
                content.append(
                    {
                        "name": item,
                        "type": "directory" if is_dir else "file",
                        "path": os.path.join(path, item),
                    }
                )

            return {"path": path, "items": content}
        except Exception as e:
            return {"error": f"Could not list directory: {str(e)}"}
