from typing import List, Optional, Dict, Any
from .registry import registry
from app.services.project_service import ProjectService
from app.core.database import AsyncSessionLocal


@registry.tool
async def create_project(project_id: str, name: str, root_path: str) -> Dict[str, Any]:
    """
    Creates a new project record in the system.
    """
    async with AsyncSessionLocal() as session:
        service = ProjectService(session)
        project = await service.create_project(project_id, name, root_path)
        return {
            "status": "success",
            "project_id": project.id,
            "message": f"Project '{name}' created successfully.",
        }


@registry.tool
async def list_projects() -> List[dict]:
    """
    Lists all projects available in the database.
    Returns a list of project objects with their id and name.
    """
    async with AsyncSessionLocal() as session:
        service = ProjectService(session)
        projects = await service.list_all_projects()
        return [{"id": p.id, "name": p.name} for p in projects]


@registry.tool
async def get_project_details(project_id: str) -> dict:
    """
    Gets full details of a specific project by its ID.
    """
    async with AsyncSessionLocal() as session:
        service = ProjectService(session)
        project = await service.get_project(project_id)
        if not project:
            return {"error": f"Project with id {project_id} not found."}
        return {
            "id": project.id,
            "name": project.name,
            "root_path": project.root_path,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
        }
