from typing import List, Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.project import Project
from .base_repository import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, session: AsyncSession):
        super().__init__(Project, session)

    async def get_with_files(self, project_id: str) -> Optional[Project]:
        """Get project and eagerly load its files."""
        # Note: SQLModel Relationship handles this, but we can be explicit if needed
        return await self.get_by_id(project_id)
