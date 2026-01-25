from typing import List, Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.relation import Relation
from app.storage.relation_repository import RelationRepository


class RelationService:
    def __init__(self, session: AsyncSession):
        self.repo = RelationRepository(session)

    async def create_relation(
        self,
        project_id: str,
        from_node: str,
        to_node: str,
        relation_type: str,
        source: Optional[str] = None,
    ) -> Relation:
        """Registers a relationship between two nodes (e.g. function calls, inheritance)."""
        relation = Relation(
            project_id=project_id,
            from_node=from_node,
            to_node=to_node,
            relation=relation_type,
            source=source,
        )
        return await self.repo.create(relation)

    async def get_project_relations(self, project_id: str) -> List[Relation]:
        """Retrieves all relations within a project."""
        return await self.repo.get_by_project(project_id)
