import os
from collections import defaultdict
from typing import Dict, Any, Optional, List, Callable

from app.agents.core.base import BaseLLMClient
from app.agents.agent_executor import AgentExecutor
from app.core.logger import get_logger
from app.agents.architect.schema import WikiPageDetail
from .prompts import SCRIBE_ARCHITECTURE_PROMPT, SCRIBE_REFERENCE_PROMPT
from app.core.tokenizer import Tokenizer

logger = get_logger(__name__)


class ScribeAgent:
    def __init__(self, client: BaseLLMClient, on_event: Optional[Callable] = None):
        self.client = client
        self.on_event = on_event

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

    async def _prepare_facts(
        self, modules_map: Dict[str, List[Any]], target_modules: List[str]
    ) -> str:
        """Concatenate facts for the target modules.
        Uses fuzzy matching because target_modules are page IDs (e.g. 'modules-scanner')
        while modules_map keys are directory paths (e.g. 'ira/app/modules/scanner').
        """
        text = ""

        for mod_target in target_modules:
            # Normalize the target: 'modules-scanner' -> ['modules', 'scanner']
            target_parts = mod_target.lower().replace("_", "-").split("-")

            for mod_key, mod_files in modules_map.items():
                # Normalize the module path: 'ira/app/modules/scanner' -> ['ira', 'app', 'modules', 'scanner']
                key_parts = mod_key.lower().replace("\\", "/").split("/")

                # Match if ALL target parts appear in the key path
                if all(part in key_parts for part in target_parts):
                    text += f"=== MODULE: {mod_key} ===\n"
                    for f in mod_files:
                        fname = f.get("file", "")
                        text += f"\nFILE: {fname}\n"
                        for c in f.get("conclusions", []):
                            text += f"- [{c.get('topic')}]: {c.get('statement')}\n"

        # Fallback: if no matches found, do NOT include all facts to save cost.
        if not text:
            text = "No specific technical facts found for this module."
            logger.warning(
                f"No matching modules found for targets: {target_modules}. Sending empty context."
            )

        return text

    async def write_page(
        self,
        page_id: str,
        page_type: str,  # 'page' (generic), 'architecture_overview', 'module_reference'
        page_title: str,
        target_modules: List[str],
        miner_output: Dict[str, Any],
    ) -> Optional[WikiPageDetail]:
        """
        Generates the content for a single wiki page.
        """
        logger.info(
            f"Scribe is writing page '{page_title}' ({page_type}). Target modules: {target_modules}"
        )

        # 1. Prepare Context
        raw_results = miner_output.get("results", [])
        modules_map = self._group_by_module(raw_results)

        relevant_facts = await self._prepare_facts(modules_map, target_modules)

        # Safety Limit (Tokens)
        # GPT-4o-mini has 128k context. Let's reserve 20k for output/system prompts.
        # So we can safely use ~100k input tokens.
        MAX_INPUT_TOKENS = 100_000

        relevant_facts = Tokenizer.truncate(relevant_facts, MAX_INPUT_TOKENS)

        # 2. Select Prompt
        if "overview" in page_type.lower() or "architecture" in page_title.lower():
            system_prompt = SCRIBE_ARCHITECTURE_PROMPT
        else:
            system_prompt = SCRIBE_REFERENCE_PROMPT

        executor = AgentExecutor(client=self.client, on_event=self.on_event)
        executor.set_system_prompt(system_prompt)

        user_msg = f"Page Title: {page_title}\n\nTECHNICAL FACTS:\n{relevant_facts}"
        executor.add_user_message(user_msg)

        # 3. Output Schema
        submit_tool = {
            "type": "function",
            "function": {
                "name": "submit_page",
                "description": "Submit generated page content.",
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
                # Ensure the ID from argument matches result or force it?
                # Ideally the LLM respects it, but let's override to be safe.
                page_data = WikiPageDetail(**result["data"])
                if page_data.id != page_id:
                    page_data.id = page_id  # Enforce consistency
                return page_data
        except Exception as e:
            logger.error(f"Scribe failed to write page {page_id}: {e}")

        return None
