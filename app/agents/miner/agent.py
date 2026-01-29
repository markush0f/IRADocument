from typing import Dict, Any, Optional
import json
from app.agents.core.base import BaseLLMClient
from app.agents.agent_executor import AgentExecutor
from app.core.logger import get_logger
from .prompts import MINER_SYSTEM_PROMPT
from .schema import MinerOutput

logger = get_logger(__name__)


class MinerAgent:
    def __init__(self, client: BaseLLMClient):
        self.client = client
        self.executor = AgentExecutor(client=client)
        self.executor.set_system_prompt(MINER_SYSTEM_PROMPT)

    async def analyze_file(
        self, file_path: str, file_content: str
    ) -> Optional[MinerOutput]:
        """
        Analyzes a single file and extracts conclusions using Tool Calling.
        """
        user_message = (
            f"File Context:\nPath: {file_path}\nContent:\n```\n{file_content}\n```"
        )
        self.executor.add_user_message(user_message)

        # 1. Define the tool definition schema (OpenAI/Ollama format)
        submit_tool_def = {
            "type": "function",
            "function": {
                "name": "submit_conclusions",
                "description": "Submit the extracted conclusions from the file analysis.",
                "parameters": miner_output_schema,
            },
        }

        # 2. Define the callback - acts as a simpler data capturer
        # We use a Future or a simple container to "catch" the result
        extraction_result = {"data": None}

        def submit_conclusions(**kwargs):
            # Flexible argument handling to robustly capture data from LLM
            # The LLM might pass arguments flattened or nested

            # Extract file path
            file_val = kwargs.get("file", file_path)

            # Extract conclusions
            conclusions_val = kwargs.get("conclusions", [])

            # If the LLM passed a single conclusion flattened (common mistake), wrap it
            if not conclusions_val and "topic" in kwargs:
                conclusions_val = [
                    {
                        "topic": kwargs.get("topic"),
                        "impact": kwargs.get("impact"),
                        "statement": kwargs.get("statement"),
                    }
                ]

            logger.info(f"Received {len(conclusions_val)} conclusions for {file_val}")
            extraction_result["data"] = {
                "file": file_val,
                "conclusions": conclusions_val,
            }
            return "Conclusions successfully submitted."

        # 3. Register the tool
        self.executor.register_tool(submit_tool_def, submit_conclusions)

        try:
            # 4. Run the Agent - expecting it to call our tool
            last_response = await self.executor.run_until_complete()
            logger.info(f"DEBUG - Raw Response: {last_response}")

            # 5. Retrieve the captured data
            if extraction_result["data"]:
                return MinerOutput(**extraction_result["data"])

            # 6. Fallback: Check if the model just wrote the JSON in the text
            logger.warning(
                f"Miner finished but did not call submit_conclusions for {file_path}. Attempting fallback."
            )

            # Try to grab content from the response string directly
            content = last_response if isinstance(last_response, str) else ""
            if not content and isinstance(last_response, dict):
                content = last_response.get("content", "")

            if content:
                import re

                # Try to find JSON block: either purely { ... } or ```json { ... } ```
                # We look for the "conclusions" key as a strong signal
                match = re.search(r"(\{.*\})", content.replace("\n", " "), re.DOTALL)

                if match:
                    try:
                        json_str = match.group(1)
                        data = json.loads(json_str)

                        # HANDLE RAW TOOL CALL STRUCTURE
                        # If the model returned {"name": "submit_conclusions", "arguments": {...}}
                        if "arguments" in data and isinstance(data["arguments"], dict):
                            data = data["arguments"]

                        # Normalize data
                        if "file" not in data:
                            data["file"] = file_path

                        # Validate via Pydantic
                        return MinerOutput(**data)
                    except Exception as parse_err:
                        logger.error(f"Fallback parse failed: {parse_err}")

            return None

        except Exception as e:
            logger.error(f"Miner failed to analyze {file_path}: {e}")
            return None


# Helper to generate JSON Schema from Pydantic
miner_output_schema = MinerOutput.model_json_schema()
