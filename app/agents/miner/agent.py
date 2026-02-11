from typing import Dict, Any, Optional, List, Tuple
import json
from app.agents.core.base import BaseLLMClient
from app.agents.agent_executor import AgentExecutor
from app.core.logger import get_logger
from .prompts import MINER_SYSTEM_PROMPT
from .schema import MinerOutput, MinerBatchOutput

logger = get_logger(__name__)


from typing import Dict, Any, Optional, List, Tuple, Callable


class MinerAgent:
    """
    The Miner Agent creates 'Atomic Facts' from source code.

    It wraps an AgentExecutor to facilitate LLM interaction with a specific
    system prompt and toolset designed for code analysis.

    Key Responsibilities:
    - Analyze individual or batched source files.
    - extract structured 'MinerOutput' containing conclusions about the code.
    - Ensure isolation between file analyses to prevent context leakage and high token costs.
    """

    def __init__(self, client: BaseLLMClient, on_event: Optional[Callable] = None):
        self.client = client
        self.executor = AgentExecutor(client=client, on_event=on_event)
        self.executor.set_system_prompt(MINER_SYSTEM_PROMPT)

    async def analyze_file(
        self, file_path: str, file_content: str
    ) -> Optional[MinerOutput]:
        """
        Analyzes a single source file to extract key architectural conclusions.

        This method:
        1. Resets the executor state to ensure a clean context window (CRITICAL for cost).
        2. Injects the file content into the prompt.
        3. Forces the LLM to use the `submit_conclusions` tool.
        4. Returns the structured output or attempts a fallback parsing if tool calling fails.
        """
        # CRITICAL: Reset executor state to prevent message accumulation across files
        # Without this, each file analysis carries the ENTIRE history of all previous files,
        # causing token usage to grow exponentially and multiply costs dramatically.
        self.executor.set_system_prompt(MINER_SYSTEM_PROMPT)
        self.executor.tools_definitions = []
        self.executor.tools_registry = {}

        user_message = (
            f"File Context:\nPath: {file_path}\nContent:\n```\n{file_content}\n```"
        )
        self.executor.add_user_message(user_message)

        # 1. Add instruction to force standardized output
        self.executor.add_user_message(
            "Analyze the code above and submit your conclusions immediately using the 'submit_conclusions' tool."
        )

        # 2. Define the tool definition schema (OpenAI/Ollama format)
        submit_tool_def = {
            "type": "function",
            "function": {
                "name": "submit_conclusions",
                "description": "Submit the extracted conclusions from the file analysis.",
                "parameters": miner_output_schema,
            },
        }

        # 3. Define the callback
        extraction_result = {"data": None}

        def submit_conclusions(**kwargs):
            # Flexible argument handling
            # Extract file path
            file_val = kwargs.get("file", file_path)

            # Extract conclusions
            conclusions_val = kwargs.get("conclusions", [])

            # Wrap single conclusion if necessary
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

        # 4. Register the tool
        self.executor.register_tool(submit_tool_def, submit_conclusions)

        try:
            # 5. Run the Agent
            last_response = await self.executor.run_until_complete()
            logger.info(f"DEBUG - Raw Response: {last_response}")

            # 6. Retrieve the captured data
            if extraction_result["data"]:
                return MinerOutput(**extraction_result["data"])

            # 7. Fallback Logic
            logger.warning(
                f"Miner finished but did not call submit_conclusions for {file_path}. Attempting fallback."
            )

            # Try to grab content from the response string directly
            content = last_response if isinstance(last_response, str) else ""
            if not content and isinstance(last_response, dict):
                content = last_response.get("content", "")

            if content:
                import re

                # Try to find JSON block
                match = re.search(r"(\{.*\})", content.replace("\n", " "), re.DOTALL)

                if match:
                    try:
                        json_str = match.group(1)
                        data = json.loads(json_str)

                        # Handle raw tool call structure wrapper
                        if "arguments" in data and isinstance(data["arguments"], dict):
                            data = data["arguments"]
                        elif "parameters" in data and isinstance(
                            data["parameters"], dict
                        ):
                            data = data["parameters"]

                        # Normalize data
                        if "file" not in data:
                            data["file"] = file_path

                        return MinerOutput(**data)
                    except Exception as parse_err:
                        logger.error(f"Fallback parse failed: {parse_err}")

            return None

        except Exception as e:
            logger.error(f"Miner failed to analyze {file_path}: {e}")
            return None

    async def analyze_batch(
        self, files: List[Tuple[str, str]]
    ) -> Optional[MinerBatchOutput]:
        """
        Analyzes a batch of files and extracts conclusions in a single shot.
        files: List of (file_path, file_content) tuples
        """
        # 1. Reset executor for new session
        self.executor.messages = [{"role": "system", "content": MINER_SYSTEM_PROMPT}]

        # 2. Build Multi-File Context
        context_str = "Analyze the following files:\n\n"
        for path, content in files:
            context_str += f"=== FILE: {path} ===\n{content}\n====================\n\n"

        self.executor.add_user_message(context_str)

        # 3. Define the Batch Tool
        submit_tool_def = {
            "type": "function",
            "function": {
                "name": "submit_batch_results",
                "description": "Submit conclusions for multiple files at once.",
                "parameters": miner_batch_schema,
            },
        }

        # 4. Callback
        extraction_result = {"data": None}

        def submit_batch_results(**kwargs):
            # Handle results key
            results = kwargs.get("results", [])
            logger.info(f"Received batch results for {len(results)} files.")
            extraction_result["data"] = {"results": results}
            return "Batch submitted."

        self.executor.register_tool(submit_tool_def, submit_batch_results)

        try:
            # 5. Execute
            last_response = await self.executor.run_until_complete()
            logger.info(f"DEBUG Batch Response: {last_response}")

            if extraction_result["data"]:
                return MinerBatchOutput(**extraction_result["data"])

            # 6. Fallback (Similar logic but for batch)
            content = last_response if isinstance(last_response, str) else ""
            if not content and isinstance(last_response, dict):
                content = last_response.get("content", "")

            if content:
                import re

                # Look for 'results' key
                match = re.search(
                    r"(\{.*\"results\".*\})", content.replace("\n", " "), re.DOTALL
                )
                if match:
                    try:
                        json_str = match.group(1)
                        data = json.loads(json_str)
                        # Handle parameters/arguments wrapper
                        if "arguments" in data:
                            data = data["arguments"]
                        elif "parameters" in data:
                            data = data["parameters"]

                        return MinerBatchOutput(**data)
                    except Exception as e:
                        logger.error(f"Batch fallback failed: {e}")

            return None

        except Exception as e:
            logger.error(f"Batch analysis failed: {e}")
            return None


# Helper to generate JSON Schema from Pydantic
from .schema import MinerBatchOutput

miner_output_schema = MinerOutput.model_json_schema()
miner_batch_schema = MinerBatchOutput.model_json_schema()
