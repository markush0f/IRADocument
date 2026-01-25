from typing import List, Dict, Any
from app.agents.tools.registry import registry
from app.services.discovery_service import DiscoveryService
from app.core.database import AsyncSessionLocal


@registry.tool
async def register_discovery(
    project_id: str,
    discovery_type: str,
    source: str,
    name: str,
    details: Dict[str, Any] = None,
    confidence: float = 1.0,
) -> Dict[str, Any]:
    """
    Registers a new finding or technology discovered in the project.
    Use this to save information like: frameworks used, database types, or architectural components.

    Args:
        project_id: The ID of the project.
        discovery_type: Category of the discovery (e.g., 'framework', 'database', 'language').
        source: Where this info comes from (e.g., 'package.json', 'source_code_analysis').
        name: Name of the discovered item (e.g., 'React', 'FastAPI').
        details: Optional dictionary with extra info (e.g., {'version': '18.2.0'}).
        confidence: A value between 0 and 1 indicating how certain we are.
    """
    payload = {"name": name}
    if details:
        payload.update(details)

    async with AsyncSessionLocal() as session:
        service = DiscoveryService(session)
        fact = await service.register_discovery(
            project_id=project_id,
            discovery_type=discovery_type,
            source=source,
            payload=payload,
            confidence=confidence,
        )
        return {
            "status": "success",
            "fact_id": fact.id,
            "message": f"Registered {discovery_type}: {name}",
        }


@registry.tool
async def list_project_discoveries(project_id: str) -> List[Dict[str, Any]]:
    """
    Lists all technologies and facts discovered for a specific project.
    """
    async with AsyncSessionLocal() as session:
        service = DiscoveryService(session)
        facts = await service.get_project_discoveries(project_id)

        results = []
        for f in facts:
            results.append(
                {
                    "id": f.id,
                    "type": f.type,
                    "source": f.source,
                    "payload": f.payload,  # This is a JSON string from the DB
                    "confidence": f.confidence,
                    "created_at": f.created_at,
                }
            )
        return results
