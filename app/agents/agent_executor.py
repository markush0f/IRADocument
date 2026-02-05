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
        on_event: Optional[Callable[[Dict[str, Any]], Any]] = None,
    ):
        self.client = client
        self.registry = registry
        self.context = context or {}
        self.on_event = on_event
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

    async def _emit(self, event_type: str, data: Any):
        if self.on_event:
            event = {"type": "agent_thought", "subtype": event_type, "data": data}
            if asyncio.iscoroutinefunction(self.on_event):
                await self.on_event(event)
            else:
                self.on_event(event)

    async def run_step(self) -> Dict[str, Any]:
        """
        Performs a single execution step: Chat -> Tool Execution -> History Update.
        Returns the LLM's response message after tool executions (if any).
        """
        tools = self._get_tools_definitions()

        # 1. Ask the LLM
        await self._emit(
            "llm_request", {"messages": self.messages[-1] if self.messages else None}
        )

        response_message = await self.client.process_messages(
            self.messages, tools=tools if tools else None
        )

        await self._emit("llm_response", {"content": response_message.get("content")})

        self.messages.append(response_message)

        tool_calls = response_message.get("tool_calls", [])

        if not tool_calls and response_message.get("content"):
            tool_calls = self._parse_tool_calls_from_content(
                response_message["content"]
            )

        # 3. Execute tools
        if tool_calls:
            logger.info(f"Agent requested {len(tool_calls)} tool calls.")
            await self._emit("tool_calls", {"calls": tool_calls})

            for tool_call in tool_calls:
                result = await self._execute_tool(tool_call)

                await self._emit(
                    "tool_result",
                    {
                        "tool": tool_call.get("function", {}).get("name"),
                        "result": result,
                    },
                )

                tool_msg = {
                    "role": "tool",
                    "content": json.dumps(result),
                }
                if "id" in tool_call:
                    tool_msg["tool_call_id"] = tool_call["id"]

                self.messages.append(tool_msg)

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

        # If arguments is a JSON string (OpenAI standard), parse it.
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                # If parsing fails, pass as is (or handle error), but likely it's raw text
                # We could try to pass it as a single arg if we knew the function signature,
                # but for now let's log warning and try.
                logger.warning(f"Could not parse tool arguments as JSON: {arguments}")

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
