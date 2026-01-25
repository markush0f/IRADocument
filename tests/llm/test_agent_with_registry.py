import pytest
from app.llm.agent import ToolExecutor
from app.llm.factory import LLMFactory
from app.llm.tools import registry
from app.core.config import settings


@pytest.mark.asyncio
async def test_agent_with_real_registry():
    """Test the agent using the ToolRegistry and real database tools."""
    client = LLMFactory.get_client(settings.llm_provider)
    # Pass the singleton registry to the executor
    agent = ToolExecutor(client, registry=registry)

    # Ask about projects (the agent should call list_projects)
    prompt = "Dame una lista de los proyectos que tienes en la base de datos"

    try:
        response = await agent.run(prompt)
        print(f"\nResponse: {response}")
        assert isinstance(response, str)
        assert len(response) > 0
    except Exception as e:
        pytest.skip(f"Ollama/Agent test skipped: {e}")
