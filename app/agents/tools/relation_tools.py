from typing import List, Dict, Any, Optional
from .registry import registry
from app.services.relation_service import RelationService
from app.core.database import AsyncSessionLocal


@registry.tool
async def register_relation(
    project_id: str,
    from_node: str,
    to_node: str,
    relation_type: str,
    source: Optional[str] = None,
) -> Dict[str, Any]:
    """Registers a relationship between two components of the project."""
    async with AsyncSessionLocal() as session:
        service = RelationService(session)
        rel = await service.create_relation(
            project_id, from_node, to_node, relation_type, source
        )
        return {
            "status": "success",
            "from": rel.from_node,
            "to": rel.to_node,
            "type": rel.relation,
        }


@registry.tool
async def list_project_relations(project_id: str) -> List[Dict[str, Any]]:
    """Lists all architectural relations discovered in the project."""
    async with AsyncSessionLocal() as session:
        service = RelationService(session)
        relations = await service.get_project_relations(project_id)
        return [
            {
                "from": r.from_node,
                "to": r.to_node,
                "type": r.relation,
                "source": r.source,
            }
            for r in relations
        ]
