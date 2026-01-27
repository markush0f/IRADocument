import json
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from app.agents.agent_executor import AgentExecutor
from app.agents.core.factory import LLMFactory
from app.agents.tools import registry
from app.services.fact_service import FactService
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class AnalysisService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.fact_service = FactService(session)

    async def generate_analysis_report(
        self, project_id: str, prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point that launches the Orchestrator Agent.
        The orchestrator will decide which specialized analysis tools to run.
        """
        try:
            # 1. Initialize Orchestrator Agent
            agent = self._setup_orchestrator(project_id)

            # 2. Run Orchestrator
            user_prompt = (
                prompt or f"Perform a technical analysis of project '{project_id}'."
            )
            agent.add_user_message(user_prompt)
            final_answer = await agent.run_until_complete(max_iterations=10)

            # 3. Final summary of findings
            facts = await self.fact_service.get_facts_by_project(project_id)

            return {
                "project_id": project_id,
                "orchestrator_conclusion": final_answer,
                "discoveries_count": len(facts),
                "status": "completed",
            }

        except Exception as e:
            logger.error(f"Orchestration failed for project {project_id}: {str(e)}")
            return {"project_id": project_id, "error": str(e), "status": "failed"}

    def _setup_orchestrator(self, project_id: str) -> AgentExecutor:
        """Configures the Orchestrator Agent with high-level analysis tools."""
        client = LLMFactory.get_client(settings.llm_provider, model="qwen2.5-coder:3b")
        agent = AgentExecutor(
            client, registry=registry, context={"project_id": project_id}
        )

        # The orchestrator only sees high-level analysis tools
        orchestrator_tools = [
            "analyze_tech_stack",
            "browse_repository",
            "list_project_facts",
        ]
        agent._get_tools_definitions = lambda: registry.get_definitions_by_names(
            orchestrator_tools
        )

        # Set orchestrator persona
        system_prompt = f"""
        You are the Project Analysis Orchestrator. Your mission is to analyze project '{project_id}'.
        
        You have several specialized tools (sub-agents) to help you:
        - 'browse_repository': To understand structure and architecture.
        - 'analyze_tech_stack': To identify technologies and dependencies.
        - 'list_project_facts': To check existing findings.
        
        Decide which tool to use based on the current state of the analysis and the user's request.
        """
        agent.set_system_prompt(system_prompt)
        return agent
