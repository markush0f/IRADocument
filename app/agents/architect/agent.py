import json
import os
from collections import defaultdict
from typing import Dict, Any, Optional, List

from app.agents.core.base import BaseLLMClient
from app.agents.agent_executor import AgentExecutor
from app.core.logger import get_logger
from .prompts import ARCHITECT_NAVIGATION_PROMPT, ARCHITECT_PAGE_WRITER_PROMPT
from .schema import WikiNavigation, WikiPageDetail

logger = get_logger(__name__)


class ArchitectAgent:
    def __init__(self, client: BaseLLMClient):
        self.client = client

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

    async def _summarize_module_for_context(
        self, module_name: str, files: List[Dict[str, Any]]
    ) -> str:
        """Create a summary used for Navigation Planning."""
        # Lightweight summary
        prompt = f"Summarize module '{module_name}' with {len(files)} files. What is its main responsibility?"
        # Simple concat of topics for context
        topics = set()
        for f in files:
            for c in f.get("conclusions", []):
                topics.add(c.get("topic"))

        context = f"Module: {module_name}\nFiles: {len(files)}\nTopics: {', '.join(list(topics)[:10])}"
        return context

    async def _prepare_module_facts(
        self, module_name: str, files: List[Dict[str, Any]]
    ) -> str:
        """Prepare FULL DETAILED facts for Page Writing."""
        text = f"=== MODULE: {module_name} ===\n"
        for f in files:
            fname = os.path.basename(f.get("file", ""))
            text += f"\nFILE: {fname}\n"
            for c in f.get("conclusions", []):
                text += f"- [{c.get('topic')}]: {c.get('statement')}\n"
        return text

    async def plan_navigation(
        self, miner_output: Dict[str, Any]
    ) -> Optional[WikiNavigation]:
        """
        Step 1: Analyze structure and propose a Sidebar Tree.
        """
        raw_results = miner_output.get("results", [])
        modules_map = self._group_by_module(raw_results)

        # Create a "System Overview" for the Architect
        overview_text = "Project Modules:\n"
        for mod, files in modules_map.items():
            overview_text += f"- {mod} ({len(files)} files)\n"

        logger.info("Architect is planning navigation tree...")

        executor = AgentExecutor(client=self.client)
        executor.set_system_prompt(ARCHITECT_NAVIGATION_PROMPT)
        executor.add_user_message(
            f"Here is the project structure. Design the Wiki Navigation.\n\n{overview_text}"
        )

        # Tool
        submit_tool = {
            "type": "function",
            "function": {
                "name": "submit_navigation",
                "description": "Submit navigation tree.",
                "parameters": WikiNavigation.model_json_schema(),
            },
        }

        result = {"data": None}

        def submit_navigation(**kwargs):
            result["data"] = kwargs
            return "Saved."

        executor.register_tool(submit_tool, submit_navigation)

        try:
            await executor.run_until_complete(max_iterations=2)
            if result["data"]:
                return WikiNavigation(**result["data"])
        except Exception as e:
            logger.error(f"Navigation planning failed: {e}")

        return None

    async def write_page(
        self,
        page_id: str,
        page_title: str,
        related_modules: List[str],
        miner_output: Dict[str, Any],
    ) -> Optional[WikiPageDetail]:
        """
        Step 2: Write a specific page in full detail.
        """
        raw_results = miner_output.get("results", [])
        modules_map = self._group_by_module(raw_results)

        # Gather ALL facts relevant to this page
        # If page_id is 'services', we want facts from 'app/services'
        # Heuristic: Match page_id/title keywords against module names
        relevant_facts = ""

        # Simple heuristic mapping for now (can be improved)
        # We pass ALL module summaries if unsure, or specific ones.
        # For 'Deep Dive', let's pass specific module content if matched, or everything if 'Overview'.

        # Better approach: We pass the page_id and let the heuristic find data.
        # For this prototype, I will dump relevant modules.

        target_modules = []
        for mod in modules_map.keys():
            # If the module name is in the page_id (e.g. 'services' in 'services-overview')
            # Or if it's a generic page, we might need broader context.
            if mod in page_id or page_id in mod or page_id == "architecture":
                target_modules.append(mod)

        # If no specific match, maybe it's a high level page, send core summaries?
        if not target_modules:
            target_modules = list(
                modules_map.keys()
            )  # All context (expensive but safe)

        logger.info(
            f"Writing page '{page_title}' using context from {len(target_modules)} modules..."
        )

        for mod in target_modules:
            relevant_facts += (
                await self._prepare_module_facts(mod, modules_map[mod]) + "\n"
            )

        # Executor
        executor = AgentExecutor(client=self.client)
        # Inject page title into prompt
        prompt = ARCHITECT_PAGE_WRITER_PROMPT.replace("{page_title}", page_title)
        executor.set_system_prompt(prompt)

        executor.add_user_message(
            f"Write the page content.\n\nSOURCE MATERIAL:\n{relevant_facts[:100000]}"
        )  # Truncate safety

        # Tool
        submit_tool = {
            "type": "function",
            "function": {
                "name": "submit_page",
                "description": "Submit page content.",
                "parameters": WikiPageDetail.model_json_schema(),
            },
        }

        result = {"data": None}

        def submit_page(**kwargs):
            result["data"] = kwargs
            return "Saved."

        executor.register_tool(submit_tool, submit_page)

        try:
            await executor.run_until_complete(max_iterations=2)
            if result["data"]:
                return WikiPageDetail(**result["data"])
        except Exception as e:
            logger.error(f"Page writing failed: {e}")

        return None
