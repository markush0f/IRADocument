import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlmodel.ext.asyncio.session import AsyncSession
from app.agents.executor import ToolExecutor
from app.agents.core.factory import LLMFactory
from app.agents.tools import registry
from app.services.fact_service import FactService
from app.core.config import settings


class AnalysisService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.fact_service = FactService(session)

    async def generate_analysis_report(self, project_id: str) -> Dict[str, Any]:
        """
        Coordinates an agent to analyze a project and generate a discovery report.
        The agent will discover technologies and save them as Facts.
        """
        client = LLMFactory.get_client(settings.llm_provider, model="qwen2.5-coder:3b")
        # Exclude self-referencing analysis tool to avoid infinite loops
        agent = ToolExecutor(
            client, registry=registry, context={"project_id": project_id}
        )

        # We manually filter the definitions or tell the executor to ignore it
        def filtered_get_definitions():
            return [
                d
                for d in registry.get_definitions()
                if d["function"]["name"] != "run_project_analysis"
            ]

        agent._get_tools_definitions = filtered_get_definitions

        system_prompt = f"""
        You are a tool-calling bot. Analyze project '{project_id}'.
        
        MANDATORY RULES:
        1. YOU MUST USE project_id='{project_id}' for all tool calls.
        2. DO NOT call 'create_project'. The project already exists.
        3. FOR EACH technology, framework, or library you find (e.g., FastAPI, SQLAlchemy, React, Python), YOU MUST CALL 'register_fact'.
        4. DO NOT just list them in text. Each discovery MUST be a separate tool call.
        5. START by calling 'list_directory_content' with path="".
        6. READ config files (requirements.txt, package.json, etc) to find versions.
        7. FINISH by calling 'register_fact' with type='discovery_report' containing your final summary.
        
        YOUR FIRST ACTION: Call 'list_directory_content'.
        """

        user_prompt = "Please perform the analysis for the project."

        try:
            # The agent will perform multiple tool calls
            final_answer = await agent.run(
                user_prompt, system_prompt=system_prompt, max_iterations=10
            )

            # Retrieve what was saved to return a confirmation
            facts = await self.fact_service.get_facts_by_project(project_id)

            return {
                "project_id": project_id,
                "agent_conclusion": final_answer,
                "discoveries_count": len(facts),
                "status": "completed",
            }
        except Exception as e:
            return {"project_id": project_id, "error": str(e), "status": "failed"}
