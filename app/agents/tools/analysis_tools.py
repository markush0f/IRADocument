from typing import Dict, Any
from .registry import registry
from app.core.database import AsyncSessionLocal


@registry.tool
async def analyze_tech_stack(project_id: str) -> str:
    """
    Performs a deep dive into the project's technical stack (languages, frameworks, libraries).
    Use this when you need to know exactly what technologies are being used.
    """
    from app.agents.agent_executor import AgentExecutor
    from app.agents.core.factory import LLMFactory
    from app.core.config import settings

    client = LLMFactory.get_client(settings.llm_provider, model="qwen2.5-coder:3b")
    # Specialized agent for tech stack
    agent = AgentExecutor(client, registry=registry, context={"project_id": project_id})

    # Filter tools for this specific task
    tech_tools = ["list_directory_content", "read_file_content", "register_fact"]
    agent._get_tools_definitions = lambda: registry.get_definitions_by_names(tech_tools)

    prompt = f"Identify languages, frameworks and libraries in project '{project_id}'. Use tools to explore files like package.json, requirements.txt, etc. Register facts for each discovery."
    return await agent.run(prompt)


@registry.tool
async def browse_repository(project_id: str) -> str:
    """
    Explores the repository structure to understand the architecture and organization.
    Use this to get an overview of how the project is organized.
    """
    from app.agents.agent_executor import AgentExecutor
    from app.agents.core.factory import LLMFactory
    from app.core.config import settings

    client = LLMFactory.get_client(settings.llm_provider, model="qwen2.5-coder:3b")
    agent = AgentExecutor(client, registry=registry, context={"project_id": project_id})

    # Tools for exploration
    browse_tools = ["list_directory_content", "register_fact"]
    agent._get_tools_definitions = lambda: registry.get_definitions_by_names(
        browse_tools
    )

    prompt = f"Explore the directory structure of project '{project_id}' and identify the main architectural components. Register your findings."
    return await agent.run(prompt)
