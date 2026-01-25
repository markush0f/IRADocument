from typing import List, Optional
from app.llm.tools.registry import registry
from app.storage.project_repository import ProjectRepository
from app.core.database import AsyncSessionLocal


@registry.tool
async def list_projects() -> List[dict]:
    """
    Lists all projects available in the database.
    Returns a list of project objects with their id and name.
    """
    async with AsyncSessionLocal() as session:
        repo = ProjectRepository(session)
        projects = await repo.get_all()
        return [{"id": p.id, "name": p.name} for p in projects]


@registry.tool
async def get_project_details(project_id: str) -> dict:
    """
    Gets full details of a specific project by its ID.
    """
    async with AsyncSessionLocal() as session:
        repo = ProjectRepository(session)
        project = await repo.get_by_id(project_id)
        if not project:
            return {"error": f"Project with id {project_id} not found."}
        return {
            "id": project.id,
            "name": project.name,
            "root_path": project.root_path,
            "created_at": project.created_at,
        }
