import json
import asyncio
from typing import List, Dict, Any, Callable, Optional
from .core.base import BaseLLMClient
from .tools.registry import ToolRegistry
from app.core.logger import get_logger

logger = get_logger(__name__)


class ToolExecutor:
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
        """Combines manual and registry tool definitions."""
        definitions = list(self.tools_definitions)
        if self.registry:
            definitions.extend(self.registry.get_definitions())
        return definitions

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

            # 1. Ask the LLM with all available tools
            tools = self._get_tools_definitions()
            logger.info(f"Sending {len(tools)} tools to LLM")
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

    def _parse_tool_calls_from_content(self, content: str) -> List[Dict[str, Any]]:
        """Attempts to find and parse multiple JSON tool calls in the message content."""
        import re

        logger.info(f"Attempting to parse tool calls from content: {content[:100]}...")

        # Clean up markdown code blocks
        content = re.sub(r"```[a-z]*", "", content)
        content = content.replace("```", "").strip()

        found_calls = []
        i = 0
        while i < len(content):
            if content[i] == "{":
                # Try parsing from current '{' to the potential end of the string
                # We go backwards to find the longest valid JSON object starting at i
                for j in range(len(content), i + 1, -1):
                    try:
                        chunk = content[i:j]
                        if "name" in chunk:
                            data = json.loads(chunk)
                            if isinstance(data, dict) and "name" in data:
                                found_calls.append(
                                    {
                                        "function": {
                                            "name": data.get("name"),
                                            "arguments": data.get("arguments", {}),
                                        }
                                    }
                                )
                                i = j - 1  # Skip to the end of this object
                                break
                    except (json.JSONDecodeError, Exception):
                        continue
            elif content[i] == "[":
                # Similar logic for lists if any
                for j in range(len(content), i + 1, -1):
                    try:
                        chunk = content[i:j]
                        data = json.loads(chunk)
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict) and "name" in item:
                                    found_calls.append(
                                        {
                                            "function": {
                                                "name": item.get("name"),
                                                "arguments": item.get("arguments", {}),
                                            }
                                        }
                                    )
                            i = j - 1
                            break
                    except (json.JSONDecodeError, Exception):
                        continue
            i += 1

        logger.info(f"Extracted {len(found_calls)} tool calls from content")
        return found_calls

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

        # 3. Context Injection: if arguments are missing but available in context, inject them
        import inspect

        sig = inspect.signature(func)
        final_args = arguments.copy()
        for param_name in sig.parameters:
            if param_name not in final_args and param_name in self.context:
                logger.debug(
                    f"Injecting {param_name} from context into {function_name}"
                )
                final_args[param_name] = self.context[param_name]

        try:
            if asyncio.iscoroutinefunction(func):
                return await func(**final_args)
            else:
                return func(**final_args)
        except Exception as e:
            logger.error(f"Error executing tool {function_name}: {e}")
            return {"error": str(e)}
