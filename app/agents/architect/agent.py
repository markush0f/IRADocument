import json
import os
from collections import defaultdict
from typing import Dict, Any, Optional, List

from app.agents.core.base import BaseLLMClient
from app.agents.agent_executor import AgentExecutor
from app.core.logger import get_logger
from .prompts import ARCHITECT_NAVIGATION_PROMPT, ARCHITECT_PAGE_WRITER_PROMPT
from .schema import WikiNavigation, WikiPageDetail
from .subsystems import SubsystemDetector

logger = get_logger(__name__)


class ArchitectAgent:
    def __init__(self, client: BaseLLMClient):
        self.client = client
        self.detector = SubsystemDetector(client)

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

        # 1. Detect Subsystems
        detected_subsystems = await self.detector.detect(raw_results)

        subsys_text = "DETECTED SUBSYSTEMS:\n"
        for sub in detected_subsystems:
            subsys_text += f"- {sub.name} ({sub.role}) [Root: {sub.root_path}]\n"
            subsys_text += f"  Tech: {', '.join(sub.technologies)}\n"

        overview_text = "Project Modules:\n"
        for mod, files in modules_map.items():
            overview_text += f"- {mod} ({len(files)} files)\n"

        logger.info(
            f"Architect is planning navigation. Subsystems: {[s.name for s in detected_subsystems]}"
        )

        executor = AgentExecutor(client=self.client)
        executor.set_system_prompt(ARCHITECT_NAVIGATION_PROMPT)
        executor.add_user_message(
            f"Here is the project structure. Design the Wiki Navigation.\n\n{subsys_text}\n\n{overview_text}"
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

        relevant_facts = ""
        target_modules = []

        # KEYWORD MATCHING STRATEGY
        # Match page_id/title parts against module paths
        keywords = (
            page_id.replace("-", " ").lower().split() + page_title.lower().split()
        )
        unique_keywords = set(k for k in keywords if len(k) > 2)  # Ignore short words

        logger.info(
            f"Resolving context for '{page_id}' using keywords: {unique_keywords}"
        )

        for mod_path in modules_map.keys():
            # Check if any keyword matches path parts (e.g. 'agents' in 'app/agents/miner')
            if any(k in mod_path.lower() for k in unique_keywords):
                target_modules.append(mod_path)
            # Special case: 'app' module
            if "app" in unique_keywords and mod_path == "app":
                target_modules.append(mod_path)

        # FALLBACK & SAFETY
        if not target_modules:
            logger.warning(
                f"No modules matched for page '{page_id}'. Using 'app/core' default."
            )
            target_modules = ["app/core"]

        # Sort by relevance (heuristic: exact matches first?) and LIMIT
        # If we have > 5 modules, we risk context overflow.
        if len(target_modules) > 5:
            # Sort: deeper paths first? No, maybe broader paths first?
            # Let's just keep the first 5 found by keyword match
            target_modules = target_modules[:5]
            logger.warning(f"Context truncated to 5 modules: {target_modules}")

        logger.info(f"Writing page '{page_id}' using module context: {target_modules}")

        for mod in target_modules:
            if mod in modules_map:
                relevant_facts += (
                    await self._prepare_module_facts(mod, modules_map[mod]) + "\n"
                )

        # Executor
        executor = AgentExecutor(client=self.client)
        prompt = ARCHITECT_PAGE_WRITER_PROMPT.replace("{page_title}", page_title)
        executor.set_system_prompt(prompt)

        # Context safety limit
        max_context_chars = (
            60000  # Approx 15k tokens. Safe for gpt-4o-mini (128k) but good practice.
        )
        if len(relevant_facts) > max_context_chars:
            logger.warning(
                f"Context truncated from {len(relevant_facts)} to {max_context_chars} chars."
            )
            relevant_facts = relevant_facts[:max_context_chars] + "\n...(truncated)..."

        executor.add_user_message(
            f"Write the page content.\n\nSOURCE MATERIAL:\n{relevant_facts}"
        )

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
