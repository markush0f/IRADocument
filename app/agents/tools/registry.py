import inspect
import json
from typing import Any, Callable, Dict, List, Optional, Type, get_type_hints
from pydantic import BaseModel, create_model
from app.core.logger import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def tool(self, func: Callable) -> Callable:
        """
        Decorator to register a function as a tool.
        It automatically generates the JSON schema based on type hints and docstrings.
        """
        name = func.__name__
        description = func.__doc__ or "No description provided."

        # Generate JSON Schema for parameters using Pydantic
        schema = self._generate_schema(func)

        self._tools[name] = {
            "definition": {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description.strip(),
                    "parameters": schema,
                },
            },
            "func": func,
        }
        logger.debug(f"Registered tool: {name}")
        return func

    def _generate_schema(self, func: Callable) -> Dict[str, Any]:
        """Generates a JSON schema from function signature using Pydantic."""
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)

        fields = {}
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            param_type = type_hints.get(param_name, Any)
            default_value = (
                ... if param.default == inspect.Parameter.empty else param.default
            )
            fields[param_name] = (param_type, default_value)

        # Create a dynamic Pydantic model to leverage its schema generation
        model = create_model(f"{func.__name__}_params", **fields)
        schema = model.model_json_schema()

        # SQLModel/Ollama expects a slightly simpler schema format for parameters
        return {
            "type": "object",
            "properties": schema.get("properties", {}),
            "required": schema.get("required", []),
        }

    def get_definitions(
        self, exclude: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Returns the list of tool definitions for the LLM."""
        return [
            tool["definition"]
            for name, tool in self._tools.items()
            if not exclude or name not in exclude
        ]

    def get_definitions_by_names(self, names: List[str]) -> List[Dict[str, Any]]:
        """Returns definitions for specific tools by their names."""
        return [
            self._tools[name]["definition"] for name in names if name in self._tools
        ]

    def get_function(self, name: str) -> Optional[Callable]:
        """Returns the function implementation by name."""
        tool = self._tools.get(name)
        return tool["func"] if tool else None

    def save_to_json(self, file_path: str):
        """Saves current tool definitions to a JSON file."""
        definitions = self.get_definitions()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(definitions, f, indent=4, ensure_ascii=False)
        logger.info(f"exported {len(definitions)} tool definitions to {file_path}")


# Singleton instance for easy access
registry = ToolRegistry()
