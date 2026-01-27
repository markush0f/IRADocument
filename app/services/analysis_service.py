from typing import Dict, Any, List, Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from app.agents.agent_executor import AgentExecutor
from app.agents.core.factory import LLMFactory
from app.agents.core.prompt_loader import PromptLoader
from app.agents.tools import registry
from app.agents.discovery_pipeline import ProjectDiscoveryPipeline
from app.agents.core.types import AnalysisStage
from app.services.fact_service import FactService
from app.services.project_service import ProjectService
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class AnalysisService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.fact_service = FactService(session)
        self.project_service = ProjectService(session)

    async def generate_analysis_report(
        self, project_id: str, enabled_stages: Optional[List[AnalysisStage]] = None
    ) -> Dict[str, Any]:
        """
        Executes a project analysis using a dynamic discovery pipeline.
        The service now only orchestrates the setup and execution.
        """
        try:
            # 1. Fetch project to get its root_path
            project = await self.project_service.get_project(project_id)
            if not project or not project.root_path:
                raise ValueError(f"Project {project_id} not found or missing root_path")

            # 2. Setup the AI Agent
            client = LLMFactory.get_client(
                settings.llm_provider, model="qwen2.5-coder:3b"
            )
            agent = AgentExecutor(
                client, registry=registry, context={"project_id": project_id}
            )
            agent.set_system_prompt(PromptLoader.load_prompt("system_analyst"))

            # 3. Create and execute the Pipeline
            # Everything stays inside the pipeline: scanners, tools and stages
            pipeline = ProjectDiscoveryPipeline(
                agent, project_id, project.root_path, enabled_stages=enabled_stages
            )

            result = await pipeline.execute()

            # 4. Final metadata retrieval
            facts = await self.fact_service.get_facts_by_project(project_id)

            return {"status": "completed", "discoveries_count": len(facts), **result}

        except Exception as e:
            logger.error(
                f"Analysis execution failed for project {project_id}: {str(e)}"
            )
            return {"project_id": project_id, "status": "failed", "error": str(e)}
