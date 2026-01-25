from datetime import datetime, timezone
from typing import List, Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.project import Project
from app.storage.project_repository import ProjectRepository


class ProjectService:
    def __init__(self, session: AsyncSession):
        self.repo = ProjectRepository(session)

    async def create_project(self, id: str, name: str, root_path: str) -> Project:
        """Creates a new project record."""
        project = Project(
            id=id,
            name=name,
            root_path=root_path,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        return await self.repo.create(project)

    async def get_project(self, project_id: str) -> Optional[Project]:
        """Gets a project by ID."""
        return await self.repo.get_by_id(project_id)

    async def list_all_projects(self) -> List[Project]:
        """Lists all projects."""
        return await self.repo.get_all()

    async def update_project(self, project_id: str, data: dict) -> Optional[Project]:
        """Updates project metadata."""
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        return await self.repo.update(project_id, data)

    async def delete_project(self, project_id: str) -> bool:
        """Deletes a project."""
        return await self.repo.delete(project_id)
