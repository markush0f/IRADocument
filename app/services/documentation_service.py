import os
import json
import asyncio
import aiofiles
from typing import Dict, Any, List, Optional, Tuple
from app.agents.core.factory import LLMFactory
from app.agents.miner.agent import MinerAgent
from app.agents.architect.agent import ArchitectAgent
from app.agents.scribe.agent import ScribeAgent
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


from app.core.socket_manager import manager


class DocumentationService:

    async def generate_documentation(
        self, project_id: str, root_path: str, model: str = "gpt-4o-mini"
    ) -> Dict[str, Any]:
        """
        Executes the full Triad pipeline (Miner -> Architect -> Scribe) for a project.
        """
        try:
            logger.info(
                f"Starting documentation generation for project {project_id} at {root_path}"
            )
            await manager.broadcast(
                project_id,
                {
                    "type": "pipeline_stage",
                    "stage": "started",
                    "message": "Initializing AI Agents...",
                },
            )

            # Callback for agents to emit thoughts
            async def on_agent_event(event: Dict[str, Any]):
                # Enrich with generic info if needed
                await manager.broadcast(project_id, event)

            # 1. Setup Agents
            client = LLMFactory.get_client(provider="openai", model=model)
            miner = MinerAgent(client, on_event=on_agent_event)
            architect = ArchitectAgent(client, on_event=on_agent_event)
            scribe = ScribeAgent(client, on_event=on_agent_event)

            # PHASE 1: MINING
            await manager.broadcast(
                project_id,
                {
                    "type": "pipeline_stage",
                    "stage": "mining",
                    "message": "Mining project facts...",
                },
            )
            miner_output = await self._run_miner(miner, root_path, project_id)

            # PHASE 2: PLANNING
            logger.info("Architect is planning navigation...")
            await manager.broadcast(
                project_id,
                {
                    "type": "pipeline_stage",
                    "stage": "planning",
                    "message": "Architect is designing documentation structure...",
                },
            )
            nav_plan = await architect.plan_navigation(miner_output)
            if not nav_plan:
                raise ValueError("Architect failed to generate a navigation plan.")

            await manager.broadcast(
                project_id, {"type": "plan_generated", "plan": nav_plan.model_dump()}
            )

            # PHASE 3: WRITING
            logger.info("Scribe is starting to write pages...")
            await manager.broadcast(
                project_id,
                {
                    "type": "pipeline_stage",
                    "stage": "writing",
                    "message": "Scribe is writing documentation pages...",
                },
            )
            all_modules = self._get_unique_modules(miner_output)

            # Collect all pages to write
            pages_to_write = []
            self._collect_pages(nav_plan.tree, pages_to_write)

            total_pages = len(pages_to_write)

            # Ensure project-specific output directory
            project_docs_dir = os.path.join(self.output_dir, project_id)
            os.makedirs(project_docs_dir, exist_ok=True)

            # Save Sidebar
            plan_data = nav_plan.model_dump()
            await self._save_json(
                os.path.join(project_docs_dir, "sidebar.json"), plan_data
            )

            results = []
            for i, page in enumerate(pages_to_write):
                logger.info(f"[{i+1}/{total_pages}] Writing page: {page.label}")

                await manager.broadcast(
                    project_id,
                    {
                        "type": "pipeline_progress",
                        "stage": "writing_page",
                        "current": i + 1,
                        "total": total_pages,
                        "page_label": page.label,
                        "page_id": page.id,
                    },
                )

                target_modules = self._resolve_target_modules(
                    page.id, page.label, all_modules
                )
                page_type = self._determine_page_type(page.id, page.label)

                wiki_page = await scribe.write_page(
                    page_id=page.id,
                    page_type=page_type,
                    page_title=page.label,
                    target_modules=target_modules,
                    miner_output=miner_output,
                )

                if wiki_page:
                    await self._save_json(
                        os.path.join(project_docs_dir, f"{page.id}.json"),
                        wiki_page.model_dump(),
                    )
                    results.append({"id": page.id, "status": "success"})
                else:
                    results.append({"id": page.id, "status": "failed"})

                await asyncio.sleep(1)

            await manager.broadcast(
                project_id,
                {
                    "type": "pipeline_stage",
                    "stage": "completed",
                    "message": "Documentation generation finished.",
                },
            )

            return {
                "project_id": project_id,
                "status": "completed",
                "docs_path": project_docs_dir,
                "total_pages": len(pages_to_write),
                "pages": results,
            }

        except Exception as e:
            logger.error(f"Documentation generation failed for {project_id}: {str(e)}")
            return {"project_id": project_id, "status": "failed", "error": str(e)}

    def _determine_page_type(self, page_id: str, label: str) -> str:
        """Determines if a page is an overview or a reference."""
        if (
            "overview" in page_id
            or "architecture" in label.lower()
            or "intro" in label.lower()
        ):
            return "architecture_overview"
        return "module_reference"

    async def _run_miner(
        self, miner: MinerAgent, root_path: str, project_id: str
    ) -> Dict[str, Any]:
        """Runs the miner over the project directory."""
        logger.info("Miner is collecting facts...")
        files_to_analyze = await self._collect_files(root_path)

        total_files = len(files_to_analyze)
        await manager.broadcast(
            project_id,
            {
                "type": "pipeline_progress",
                "stage": "mining_files",
                "current": 0,
                "total": total_files,
            },
        )

        # Batch process
        all_results = []
        batch_size = 5
        for i in range(0, total_files, batch_size):
            chunk = files_to_analyze[i : i + batch_size]

            await manager.broadcast(
                project_id,
                {
                    "type": "pipeline_progress",
                    "stage": "mining_files",
                    "current": i,
                    "total": total_files,
                },
            )

            batch_result = await miner.analyze_batch(chunk)
            if batch_result:
                all_results.extend([r.model_dump() for r in batch_result.results])
            await asyncio.sleep(2)  # Rate limit

        # Final broadcast
        await manager.broadcast(
            project_id,
            {
                "type": "pipeline_progress",
                "stage": "mining_files",
                "current": total_files,
                "total": total_files,
            },
        )

        return {"total_files": total_files, "results": all_results}

    async def _collect_files(self, root_path: str) -> List[Tuple[str, str]]:
        """Scans directory and returns list of (rel_path, content)."""
        collected = []
        for root, _, files in os.walk(root_path):
            if any(skip in root for skip in ["__pycache__", ".venv", "tests", ".git"]):
                continue
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    await self._process_single_file(root_path, root, file, collected)
        return collected

    async def _process_single_file(
        self, root_path: str, root: str, file: str, collected: list
    ):
        """Reads a single file and adds to collection if not empty."""
        full_path = os.path.join(root, file)
        rel_path = os.path.relpath(full_path, root_path)
        try:
            async with aiofiles.open(full_path, "r", encoding="utf-8") as f:
                content = await f.read()
            if content.strip():
                collected.append((rel_path, content))
        except Exception as e:
            logger.warning(f"Could not read {rel_path}: {e}")

    def _collect_pages(self, nodes: List[Any], pages: List[Any]):
        """Recursively collects all 'page' nodes from the tree."""
        for node in nodes:
            if node.type == "page":
                pages.append(node)
            if node.children:
                self._collect_pages(node.children, pages)

    def _get_unique_modules(self, miner_output: Dict[str, Any]) -> List[str]:
        """Extracts unique set of module names (parent directories)."""
        all_modules = {
            os.path.dirname(item.get("file", ""))
            for item in miner_output.get("results", [])
            if os.path.dirname(item.get("file", ""))
        }
        return list(all_modules)

    def _resolve_target_modules(
        self, page_id: str, page_title: str, all_modules: List[str]
    ) -> List[str]:
        """Matches a page to potential code modules using keywords."""
        keywords = (
            page_id.replace("-", " ").lower().split() + page_title.lower().split()
        )
        unique_keywords = set(k for k in keywords if len(k) > 2)

        targets = []
        for mod in all_modules:
            if any(k in mod.lower() for k in unique_keywords):
                targets.append(mod)

        # Fallback for broad pages
        if not targets and "backend" in unique_keywords:
            return ["app"] if "app" in all_modules else all_modules[:1]

        return targets[:5]

    async def _save_json(self, path: str, data: Dict[str, Any]):
        """Saves data to a JSON file in the output directory."""
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, indent=2))
        logger.info(f"Saved: {path}")
