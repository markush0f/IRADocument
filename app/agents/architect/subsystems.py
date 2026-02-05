from typing import List, Dict, Any
from pydantic import BaseModel, Field
from app.agents.core.base import BaseLLMClient
from app.agents.agent_executor import AgentExecutor
from app.core.logger import get_logger
from .prompts import SUBSYSTEM_DETECTION_PROMPT
from app.core.tokenizer import Tokenizer

logger = get_logger(__name__)


class Subsystem(BaseModel):
    name: str = Field(..., description="Name of the subsystem.")
    role: str = Field(
        ...,
        description="Role: 'backend', 'frontend', 'cli', 'database', 'infrastructure', 'library'.",
    )
    technologies: List[str] = Field(
        default_factory=list, description="Major techs used (e.g. FastAPI, React)."
    )
    root_path: str = Field(
        ..., description="Root directory of this subsystem (e.g. 'app' or 'frontend')."
    )


class SubsystemsList(BaseModel):
    subsystems: List[Subsystem]


class SubsystemDetector:
    """
    Uses LLM to analyze file structure and detect subsystems.
    """

    def __init__(self, client: BaseLLMClient):
        self.client = client

    async def detect(self, files: List[Dict[str, Any]]) -> List[Subsystem]:
        logger.info("Detecting subsystems using AI...")

        # Prepare Context
        context_lines = []
        for f in files:
            path = f.get("file", "")
            context_lines.append(f"File: {path}")
            # Add top 2 conclusions if any (to help detect technologies)
            conclusions = f.get("conclusions", [])
            for c in conclusions[:2]:
                context_lines.append(f"  - Fact: {c.get('statement')}")

        context_str = "\n".join(context_lines)

        # Safety Limit (Tokens)
        MAX_DETECTOR_TOKENS = 50_000  # Subsystem detection keeps it lighter
        context_str = Tokenizer.truncate(context_str, MAX_DETECTOR_TOKENS)

        executor = AgentExecutor(client=self.client)
        executor.set_system_prompt(SUBSYSTEM_DETECTION_PROMPT)
        executor.add_user_message(f"Analyze this codebase structure:\n\n{context_str}")

        submit_tool = {
            "type": "function",
            "function": {
                "name": "submit_subsystems",
                "description": "Submit detected subsystems.",
                "parameters": SubsystemsList.model_json_schema(),
            },
        }

        result = {"data": None}

        def submit_subsystems(**kwargs):
            result["data"] = kwargs
            return "Saved."

        executor.register_tool(submit_tool, submit_subsystems)

        try:
            await executor.run_until_complete(max_iterations=1)
            if result["data"]:
                data = SubsystemsList(**result["data"])
                # Add 'related_files' logic?
                # The LLM doesn't return full file lists to save tokens.
                # We can deduce related_files by root_path later or ask LLM for it if needed.
                # For now, let's keep the Subsystem object simple.
                return data.subsystems
        except Exception as e:
            logger.error(f"Subsystem detection failed: {e}")

        return []
