from typing import List, Dict, Any, Optional
from app.agents.agent_executor import AgentExecutor
from app.agents.tools import registry
from app.core.logger import get_logger

logger = get_logger(__name__)


class BasePipeline:
    """
    Manages a sequential flow of analysis stages (the 'ladder').
    Each stage uses a stateful AgentExecutor to build upon previous findings.
    """

    def __init__(self, agent: AgentExecutor):
        self.agent = agent
        self.stages_results: Dict[str, Any] = {}

    async def run_stage(
        self, name: str, prompt: str, tools: Optional[List[str]] = None
    ):
        """
        Executes a single stage of the ladder.

        Args:
            name: Name of the stage.
            prompt: Specific instructions for this stage.
            tools: List of allowed tool names for this stage.
        """
        logger.info(f"Starting Pipeline Stage: {name}")

        # 1. Limit tools if specified for this stage
        if tools:
            self.agent._get_tools_definitions = (
                lambda: registry.get_definitions_by_names(tools)
            )
        else:
            # If no specific tools, use all available
            self.agent._get_tools_definitions = lambda: (
                self.agent.tools_definitions + registry.get_definitions()
            )

        # 2. Inject the stage instruction into the agent's memory
        self.agent.add_user_message(prompt)

        # 3. Let the agent work until it reaches a conclusion for this stage
        result = await self.agent.run_until_complete()

        self.stages_results[name] = result
        logger.info(f"Stage '{name}' completed.")
        return result

    async def execute(self, *args, **kwargs):
        """
        This method must be implemented by subclasses to define their specific ladder.
        """
        raise NotImplementedError("Subclasses must implement the execute method.")
