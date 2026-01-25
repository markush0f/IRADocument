import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.fact import Fact
from app.storage.fact_repository import FactRepository


class FactService:
    def __init__(self, session: AsyncSession):
        self.repo = FactRepository(session)

    async def create_fact(
        self,
        project_id: str,
        fact_type: str,
        source: str,
        payload: Dict[str, Any],
        confidence: float = 1.0,
    ) -> Fact:
        """Registers a new fact in the database."""
        fact = Fact(
            id=str(uuid.uuid4()),
            project_id=project_id,
            type=fact_type,
            source=source,
            payload=json.dumps(payload),
            confidence=confidence,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        return await self.repo.create(fact)

    async def get_facts_by_project(self, project_id: str) -> List[Fact]:
        """Retrieves all facts for a project."""
        return await self.repo.get_by_project(project_id)

    async def register_technology_stack_facts(
        self, project_id: str, stack: Dict[str, List[str]], source: str = "scanner"
    ):
        """Registers multiple technology facts at once."""
        facts = []
        for component_type, techs in stack.items():
            for tech in techs:
                fact = await self.create_fact(
                    project_id=project_id,
                    fact_type="technology",
                    source=source,
                    payload={"name": tech, "component": component_type},
                    confidence=1.0,
                )
                facts.append(fact)
        return facts
