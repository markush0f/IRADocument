import json
import asyncio
from typing import List, Dict, Any, Callable, Optional
from .core.base import BaseLLMClient
from .tools.registry import ToolRegistry
from app.core.logger import get_logger

logger = get_logger(__name__)


class AgentExecutor:
    def __init__(
        self,
        client: BaseLLMClient,
        registry: Optional[ToolRegistry] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        self.client = client
        self.registry = registry
        self.context = context or {}
        self.tools_registry: Dict[str, Callable] = {}
        self.tools_definitions: List[Dict[str, Any]] = []
        self.messages: List[Dict[str, Any]] = []

    def register_tool(self, definition: Dict[str, Any], func: Callable):
        """
        Manually registers a tool by linking its LLM-readable definition with its Python implementation.

        This is useful for adding ad-hoc tools that are not part of the global registry or tools
        that require specific local context closure.

        Args:
            definition: A dictionary containing the tool's JSON schema (name, description, parameters).
                      Must follow the OpenAI/Ollama tool calling format.
            func: The callable Python function or coroutine that implements the tool's logic.
        """
        name = definition["function"]["name"]
        self.tools_registry[name] = func
        self.tools_definitions.append(definition)

    def _get_tools_definitions(self) -> List[Dict[str, Any]]:
        """Returns all available tools from manual and dynamic registries."""
        dynamic_tools = self.registry.get_definitions() if self.registry else []
        return self.tools_definitions + dynamic_tools

    def set_system_prompt(self, system_prompt: str):
        """Initializes or resets the conversation with a system prompt."""
        self.messages = [{"role": "system", "content": system_prompt}]

    def add_user_message(self, content: str):
        """Adds a user message to the conversation history."""
        self.messages.append({"role": "user", "content": content})

    async def run_step(self) -> Dict[str, Any]:
        """
        Performs a single execution step: Chat -> Tool Execution -> History Update.
        Returns the LLM's response message after tool executions (if any).
        """
        tools = self._get_tools_definitions()

        # 1. Ask the LLM: It can return a text response OR a request to call tools.
        # We send the entire conversation history (context) and the available tools.
        response_message = await self.client.process_messages(
            self.messages, tools=tools if tools else None
        )

        # We save the LLM's response (text or tool call) to history.
        # This keeps the model informed about its own previous actions.
        self.messages.append(response_message)

        # 2. Check if the LLM wants to interact with the system via tools.
        tool_calls = response_message.get("tool_calls", [])

        # Fallback parsing for models that don't support native tool calling well.
        if not tool_calls and response_message.get("content"):
            tool_calls = self._parse_tool_calls_from_content(
                response_message["content"]
            )

        # 3. Execute the requested tools and feed the results back into the history.
        if tool_calls:
            logger.info(f"Agent requested {len(tool_calls)} tool calls.")
            for tool_call in tool_calls:
                # We execute the actual Python function linked to this tool.
                result = await self._execute_tool(tool_call)

                # IMPORTANT: We add the result back to history with role='tool'.
                # This 'closes the loop', providing the LLM with the data it requested.
                self.messages.append(
                    {
                        "role": "tool",
                        "content": json.dumps(result),
                    }
                )

        return response_message

    async def run_until_complete(self, max_iterations: int = 5) -> str:
        """
        Runs multiple steps until the agent provides a final text response without tool calls.
        """
        for i in range(max_iterations):
            logger.debug(f"Iteration {i+1}/{max_iterations}")

            response = await self.run_step()

            # If the LLM didn't ask for tools in its LAST response, and we have some content
            # we consider it a final answer.
            # Note: run_step already executed tool calls and added results,
            # so we check if the response_message ITSELF had tool calls.
            if not response.get("tool_calls") and response.get("content"):
                return response["content"]

        return "Max iterations reached without a final answer."

    async def _execute_tool(self, tool_call: Dict[str, Any]) -> Any:
        """Executes a single tool and returns its result."""
        function_name = tool_call["function"]["name"]
        arguments = tool_call["function"]["arguments"]

        logger.info(f"Executing tool: {function_name} with args: {arguments}")

        func = self.tools_registry.get(function_name)
        if not func and self.registry:
            func = self.registry.get_function(function_name)

        if not func:
            return {"error": f"Tool {function_name} not found"}

        try:
            if asyncio.iscoroutinefunction(func):
                return await func(**arguments)
            return func(**arguments)
        except Exception as e:
            logger.error(f"Error executing tool {function_name}: {e}")
            return {"error": str(e)}

    def _parse_tool_calls_from_content(self, content: str) -> List[Dict[str, Any]]:
        """Attempts to parse tool calls from a JSON-like string in the content."""
        import re

        content = re.sub(r"```[a-z]*", "", content).replace("```", "").strip()
        match_list = re.search(r"(\[.*\])", content, re.DOTALL)
        match_obj = re.search(r"(\{.*\})", content, re.DOTALL)

        found_data = None
        try:
            if match_list:
                found_data = json.loads(match_list.group(1))
            elif match_obj:
                found_data = [json.loads(match_obj.group(1))]
        except Exception:
            return []

        if found_data and isinstance(found_data, list):
            standardized = []
            for item in found_data:
                if isinstance(item, dict) and "name" in item:
                    standardized.append(
                        {
                            "function": {
                                "name": item.get("name"),
                                "arguments": item.get("arguments", {}),
                            }
                        }
                    )
            return standardized
        return []
