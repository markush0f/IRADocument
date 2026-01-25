from typing import List
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.fact import Fact
from .base_repository import BaseRepository


class FactRepository(BaseRepository[Fact]):
    def __init__(self, session: AsyncSession):
        super().__init__(Fact, session)

    async def get_by_project(self, project_id: str) -> List[Fact]:
        """Get all facts for a project."""
        statement = select(Fact).where(Fact.project_id == project_id)
        results = await self.session.exec(statement)
        return results.all()
