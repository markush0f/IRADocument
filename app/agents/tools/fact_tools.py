from typing import List, Dict, Any
import json
from .registry import registry
from app.services.fact_service import FactService
from app.core.database import AsyncSessionLocal


@registry.tool
async def register_fact(
    project_id: str,
    fact_type: str,
    source: str,
    name: str,
    details: Dict[str, Any] = None,
    confidence: float = 1.0,
) -> Dict[str, Any]:
    """
    Registers a new finding or fact discovered about the project.

    Args:
        project_id: The ID of the project.
        fact_type: Category (e.g., 'framework', 'database', 'language').
        source: Source of info (e.g., 'package.json').
        name: Name of the item (e.g., 'React').
        details: Extra info (e.g., {'version': '18.2.0'}).
    """
    payload = {"name": name}
    if details:
        payload.update(details)

    async with AsyncSessionLocal() as session:
        service = FactService(session)
        fact = await service.create_fact(
            project_id=project_id,
            fact_type=fact_type,
            source=source,
            payload=payload,
            confidence=confidence,
        )
        return {
            "status": "success",
            "fact_id": fact.id,
            "message": f"Registered fact {fact_type}: {name}",
        }


@registry.tool
async def list_project_facts(project_id: str) -> List[Dict[str, Any]]:
    """Lists all facts discovered for a specific project."""
    async with AsyncSessionLocal() as session:
        service = FactService(session)
        facts = await service.get_facts_by_project(project_id)

        results = []
        for f in facts:
            results.append(
                {
                    "id": f.id,
                    "type": f.type,
                    "source": f.source,
                    "payload": (
                        json.loads(f.payload)
                        if isinstance(f.payload, str)
                        else f.payload
                    ),
                    "confidence": f.confidence,
                    "created_at": f.created_at,
                }
            )
        return results
