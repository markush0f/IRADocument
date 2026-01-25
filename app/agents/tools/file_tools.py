from typing import List, Dict, Any, Optional
from .registry import registry
from app.services.file_service import FileService
from app.core.database import AsyncSessionLocal


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
