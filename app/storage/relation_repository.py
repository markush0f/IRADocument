from typing import List
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.relation import Relation
from .base_repository import BaseRepository


class RelationRepository(BaseRepository[Relation]):
    def __init__(self, session: AsyncSession):
        super().__init__(Relation, session)

    async def get_by_project(self, project_id: str) -> List[Relation]:
        """Get all relations for a project."""
        statement = select(Relation).where(Relation.project_id == project_id)
        results = await self.session.exec(statement)
        return results.all()
