from typing import Dict, Any, List, Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from app.agents.agent_executor import AgentExecutor
from app.agents.core.factory import LLMFactory
from app.agents.core.prompt_loader import PromptLoader
from app.agents.tools import registry
from app.agents.discovery_pipeline import ProjectDiscoveryPipeline
from app.services.fact_service import FactService
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class AnalysisService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.fact_service = FactService(session)

    async def generate_analysis_report(
        self, project_id: str, enabled_stages: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Executes a project analysis using a structured discovery pipeline.
        Prompts are loaded from external files.
        """
        try:
            # 1. Initialize the shared AgentExecutor
            client = LLMFactory.get_client(
                settings.llm_provider, model="qwen2.5-coder:3b"
            )
            agent = AgentExecutor(
                client, registry=registry, context={"project_id": project_id}
            )

            # Load system prompt from file
            system_prompt = PromptLoader.load_prompt("system_analyst")
            agent.set_system_prompt(system_prompt)

            # 2. Instantiate and run the Discovery Ladder (Pipeline) with dynamic stages
            pipeline = ProjectDiscoveryPipeline(agent)
            result = await pipeline.execute(project_id, enabled_stages=enabled_stages)

            # 3. Retrieve facts count for additional metadata
            facts = await self.fact_service.get_facts_by_project(project_id)

            return {
                "project_id": project_id,
                "status": "completed",
                "discoveries_count": len(facts),
                **result,
            }

        except Exception as e:
            logger.error(
                f"Analysis execution failed for project {project_id}: {str(e)}"
            )
            return {"project_id": project_id, "status": "failed", "error": str(e)}
