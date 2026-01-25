import json
from typing import List, Dict, Any, Callable, Optional
from .base import BaseLLMClient
from app.core.logger import get_logger

logger = get_logger(__name__)


class ToolExecutor:
    def __init__(self, client: BaseLLMClient):
        self.client = client
        self.tools_registry: Dict[str, Callable] = {}
        self.tools_definitions: List[Dict[str, Any]] = []

    def register_tool(self, definition: Dict[str, Any], func: Callable):
        """Register a tool definition and its implementation."""
        name = definition["function"]["name"]
        self.tools_registry[name] = func
        self.tools_definitions.append(definition)

    async def run(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        max_iterations: int = 5,
    ) -> str:
        """Run the agent loop: Chat -> Tool Call -> Execute -> Repeat."""
        messages = self._prepare_messages(user_prompt, system_prompt)

        for i in range(max_iterations):
            logger.debug(f"Iteration {i+1} of agent loop")

            # 1. Ask the LLM
            response_message = await self.client.chat(
                messages, tools=self.tools_definitions
            )
            messages.append(response_message)

            # 2. Check if the LLM wants to call tools
            tool_calls = response_message.get("tool_calls", [])
            if not tool_calls:
                return response_message.get("content", "")

            # 3. Execute tool calls
            await self._handle_tool_calls(messages, tool_calls)

        return "Max iterations reached without a final answer."

    def _prepare_messages(
        self, user_prompt: str, system_prompt: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Initializes the message list with system and user prompts."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        return messages

    async def _handle_tool_calls(
        self, messages: List[Dict[str, Any]], tool_calls: List[Dict[str, Any]]
    ):
        """Iterates and executes a list of tool calls."""
        for tool_call in tool_calls:
            result = await self._execute_tool(tool_call)
            messages.append(
                {
                    "role": "tool",
                    "content": json.dumps(result),
                }
            )

    async def _execute_tool(self, tool_call: Dict[str, Any]) -> Any:
        """Executes a single tool and returns its result."""
        function_name = tool_call["function"]["name"]
        arguments = tool_call["function"]["arguments"]

        logger.info(f"Executing tool: {function_name} with args: {arguments}")

        if function_name not in self.tools_registry:
            logger.warning(f"Tool {function_name} not found in registry")
            return {"error": f"Tool {function_name} not found"}

        try:
            func = self.tools_registry[function_name]
            if asyncio.iscoroutinefunction(func):
                return await func(**arguments)
            else:
                return func(**arguments)
        except Exception as e:
            logger.error(f"Error executing tool {function_name}: {e}")
            return {"error": str(e)}


import asyncio  # Needed for iscoroutinefunction check
