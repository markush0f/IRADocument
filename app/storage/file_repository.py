from typing import List
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.file import File
from .base_repository import BaseRepository


class FileRepository(BaseRepository[File]):
    def __init__(self, session: AsyncSession):
        super().__init__(File, session)

    async def get_by_project(self, project_id: str) -> List[File]:
        """Get all files belonging to a specific project."""
        statement = select(File).where(File.project_id == project_id)
        results = await self.session.exec(statement)
        return results.all()
