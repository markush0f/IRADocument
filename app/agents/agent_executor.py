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

    def register_tool(self, definition: Dict[str, Any], func: Callable):
        """Register a tool definition and its implementation manually."""
        name = definition["function"]["name"]
        self.tools_registry[name] = func
        self.tools_definitions.append(definition)

    def _get_tools_definitions(self) -> List[Dict[str, Any]]:
        """Returns all available tools from manual and dynamic registries."""
        dynamic_tools = self.registry.get_definitions() if self.registry else []
        return self.tools_definitions + dynamic_tools

    async def run(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        max_iterations: int = 5,
    ) -> str:
        """Run the agent loop: Chat -> Tool Call -> Execute -> Repeat."""
        messages = self._prepare_messages(user_prompt, system_prompt)

        for i in range(max_iterations):
            logger.debug(f"Iteration {i+1}/{max_iterations} of agent loop")

            # 1. Ask the LLM with all available tools
            tools = self._get_tools_definitions()
            logger.info(f"Sending {len(tools)} tools to LLM")
            #  Chat with LLM (DEPENDS OF INSTANTIATION OF CLIENT => ollama, openai...)
            response_message = await self.client.chat(
                messages, tools=tools if tools else None
            )
            logger.info(f"LLM Response: {response_message}")
            messages.append(response_message)

            # 2. Check if the LLM wants to call tools
            tool_calls = response_message.get("tool_calls", [])

            # Fallback: some models return tool calls as a JSON list in the content string
            if not tool_calls and response_message.get("content"):
                tool_calls = self._parse_tool_calls_from_content(
                    response_message["content"]
                )

            if not tool_calls:
                return response_message.get("content", "")

            # 3. Execute tool calls
            logger.info(f"Executing {len(tool_calls)} tool calls...")
            await self._handle_tool_calls(messages, tool_calls)
            logger.info("Tool execution finished, continuing to next iteration")

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

        # 1. Search in manual registry
        func = self.tools_registry.get(function_name)

        # 2. If not found, search in dynamic registry
        if not func and self.registry:
            func = self.registry.get_function(function_name)

        if not func:
            logger.warning(f"Tool {function_name} not found in any registry")
            return {"error": f"Tool {function_name} not found"}

        # Check if the function is async and call it accordingly
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(**arguments)
            else:
                return func(**arguments)
        except Exception as e:
            logger.error(f"Error executing tool {function_name}: {e}")
            return {"error": str(e)}

    def _parse_tool_calls_from_content(self, content: str) -> List[Dict[str, Any]]:
        """Attempts to parse tool calls from a JSON-like string or block in the message content."""
        import re

        logger.info(f"Attempting to parse tool calls from content: {content[:100]}...")

        # Clean up markdown code blocks if present
        content = re.sub(r"```[a-z]*", "", content)
        content = content.replace("```", "").strip()

        # Try to find a list [...] or a single object { ... "name": ... }
        match_list = re.search(r"(\[.*\])", content, re.DOTALL)
        match_obj = re.search(r"(\{.*\})", content, re.DOTALL)

        found_data = None
        if match_list:
            try:
                found_data = json.loads(match_list.group(1))
                logger.info("Matched JSON list in content")
            except Exception:
                pass
        elif match_obj:
            try:
                found_data = [json.loads(match_obj.group(1))]
                logger.info("Matched JSON object in content")
            except Exception:
                pass

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
            logger.info(f"Standardized {len(standardized)} tool calls from content")
            return standardized
        logger.info("No tool calls found in content")
        return []
