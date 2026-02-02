import json
import os
from collections import defaultdict
from typing import Dict, Any, Optional, List

from app.agents.core.base import BaseLLMClient
from app.agents.agent_executor import AgentExecutor
from app.core.logger import get_logger
from .prompts import ARCHITECT_SYSTEM_PROMPT
from .schema import WikiStructure  # UPDATED

logger = get_logger(__name__)


class ArchitectAgent:
    def __init__(self, client: BaseLLMClient):
        self.client = client
        self.main_system_prompt = ARCHITECT_SYSTEM_PROMPT

    def _group_by_module(self, data: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
        """Groups file analyses by their parent directory (module)."""
        modules = defaultdict(list)
        for item in data:
            file_path = item.get("file", "")
            parent_dir = os.path.dirname(file_path)
            if not parent_dir:
                parent_dir = "root"
            modules[parent_dir].append(item)
        return modules

    async def _summarize_module(
        self, module_name: str, files: List[Dict[str, Any]]
    ) -> str:
        """Generates a DETAILED technical summary for a module."""
        # We need RICH details for the wiki pages.
        conclusions_text = ""
        for f in files:
            fname = os.path.basename(f.get("file", ""))
            conclusions = f.get("conclusions", [])
            statements = [
                f"- {c.get('topic')}: {c.get('statement', '')}" for c in conclusions
            ]
            conclusions_text += f"FILE: {fname}\n" + "\n".join(statements) + "\n\n"

        prompt = (
            f"As a Senior Dev, write a comprehensive Technical Brief for the module '{module_name}'.\n"
            f"Include:\n"
            f"1. Main responsibility.\n"
            f"2. Key Classes/Functions exported.\n"
            f"3. Dependencies and Patterns used.\n"
            f"4. Any interesting details found in the files.\n\n"
            f"RAW FACTS:\n{conclusions_text}"
        )

        try:
            # Generate a rich summary (allows the final agent to write a full page)
            summary = await self.client.generate(
                prompt, system="You are a Technical Scribe. extract technical details."
            )
            return summary.strip()
        except Exception as e:
            logger.error(f"Failed to summarize module {module_name}: {e}")
            return f"Module {module_name} (Error summarizing)"

    async def generate_wiki(
        self, miner_output: Dict[str, Any]
    ) -> Optional[WikiStructure]:
        """
        Consumes Miner output and generates a full WikiStructure.
        """
        raw_results = miner_output.get("results", [])
        if not raw_results:
            return None

        # 1. Map: Group by Module
        modules_map = self._group_by_module(raw_results)
        logger.info(f"Identified {len(modules_map)} modules for Wiki generation.")

        # 2. Reduce: Create Rich Summaries
        module_summaries = {}
        for mod_name, items in modules_map.items():
            logger.info(f"Drafting content for module: {mod_name}...")
            summary = await self._summarize_module(mod_name, items)
            module_summaries[mod_name] = summary

        # 3. Final Construction (The 'Wiki Builder')
        synthesis_input = (
            "Here represents the technical knowledge base of the project:\n\n"
        )
        for mod, text in module_summaries.items():
            synthesis_input += f"=== MODULE: {mod} ===\n{text}\n\n================\n"

        logger.info("Architect is structuring the DeepWiki...")

        executor = AgentExecutor(client=self.client)
        executor.set_system_prompt(self.main_system_prompt)

        executor.add_user_message(
            f"Based on the following module briefs, generate the full WikiStructure JSON.\n"
            f"Ensure you create separate pages for major modules.\n\n"
            f"{synthesis_input}"
        )

        # Register Tool
        wiki_schema = WikiStructure.model_json_schema()
        submit_tool_def = {
            "type": "function",
            "function": {
                "name": "submit_wiki",
                "description": "Submit the final Wiki structure.",
                "parameters": wiki_schema,
            },
        }

        result_container = {"data": None}

        def submit_wiki(**kwargs):
            result_container["data"] = kwargs
            return "Wiki structure saved."

        executor.register_tool(submit_tool_def, submit_wiki)

        # Run
        try:
            # We allow a bit more context/tokens for this large task
            await executor.run_until_complete(max_iterations=2)
            if result_container["data"]:
                return WikiStructure(**result_container["data"])
            return None
        except Exception as e:
            logger.error(f"Architect Wiki Generation failed: {e}")
            return None
