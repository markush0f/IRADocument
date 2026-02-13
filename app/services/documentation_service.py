import os
import json
import asyncio
import uuid
import aiofiles
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from app.agents.core.factory import LLMFactory
from app.agents.miner.agent import MinerAgent
from app.agents.architect.agent import ArchitectAgent
from app.agents.scribe.agent import ScribeAgent
from app.core.logger import get_logger
from app.core.socket_manager import manager
from app.core.tokenizer import Tokenizer

logger = get_logger(__name__)

from app.core.constants import SKIP_DIRS, IGNORE_EXTENSIONS


class DocumentationService:
    """
    Orchestrates the AI Documentation Pipeline.

    This service manages the lifecycle of documentation generation, including:
    1. Source Code Mining: Extracting facts using MinerAgent.
    2. Architecture Planning: Structuring content using ArchitectAgent.
    3. Content Writing: Generating pages using ScribeAgent.

    It implements critical safety mechanisms:
    - Token counting and Cost Estimation (aborting if > $0.50).
    - Rate Limit protection (concurrency control).
    - Caching (resuming from existing JSON outputs).
    """

    def __init__(self):
        self.output_dir = Path("output/docs")

    async def generate_documentation(
        self,
        project_id: str,
        repo_path: str,
        provider: str = "openai",
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes the full Triad pipeline (Miner -> Architect -> Scribe) for a project.

        Args:
            project_id: Unique identifier for the project session.
            repo_path: Local filesystem path to the repository root.
            provider: LLM provider id (openai, gemini, ollama...s).
            model: Specific model name (e.g., gpt-4o-mini, gemini-1.5-flash).

        Returns:
            Dict containing status, output path, and statistics.

        Raises:
            Exception: If cost safety checks fail or critical errors occur.
        """
        logger.info(f"[Service] Starting documentation generation for {project_id}")

        try:
            # Initialize
            await self._broadcast_stage(
                project_id, "started", "Initializing documentation pipeline..."
            )
            await asyncio.sleep(0.5)

            # Create output directory
            project_output_path = self.output_dir / project_id
            project_output_path.mkdir(parents=True, exist_ok=True)

            # Get LLM client
            client = LLMFactory.get_client(provider=provider, model=model)
            event_handler = self._create_event_handler(project_id)

            # ============== PHASE 1: MINER ==============
            miner_output_file = project_output_path / "miner_output.json"
            miner_output = None

            #  Check if miner output exists (Cache)
            if miner_output_file.exists():
                logger.info(
                    f"[Service] Loading existing miner output from {miner_output_file}"
                )
                await self._broadcast_stage(
                    project_id,
                    "mining",
                    "Loading cached project analysis... (Skipping expensive mining)",
                )
                async with aiofiles.open(miner_output_file, "r", encoding="utf-8") as f:
                    content = await f.read()
                    miner_output = json.loads(content)
            else:
                await self._broadcast_stage(
                    project_id, "mining", "Analyzing source code..."
                )

                # Collect source files
                files = await self._collect_source_files(repo_path)
                logger.info(f"[Service] Found {len(files)} source files to analyze")

                if not files:
                    await self._broadcast_stage(
                        project_id, "error", "No source files found in repository"
                    )
                    return {"status": "error", "message": "No source files found"}

                total_tokens = 0
                for _, content in files:
                    total_tokens += Tokenizer.count(content)

                estimated_cost = (total_tokens / 1_000_000) * 0.15

                MAX_COST_USD = 0.50

                logger.info(
                    f"[Safety] Total tokens to analyze: {total_tokens}. Estimated input cost: ${estimated_cost:.4f}"
                )

                if estimated_cost > MAX_COST_USD:
                    msg = f"SAFETY BREAK: Estimated cost ${estimated_cost:.2f} exceeds limit of ${MAX_COST_USD}"
                    logger.error(msg)
                    await self._broadcast_stage(project_id, "error", msg)
                    return {"status": "error", "message": msg}

                miner = MinerAgent(client, on_event=event_handler)
                miner_results = []

                CONCURRENCY_LIMIT = 2
                semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
                total_files = len(files)

                async def analyze_with_limit(idx, file_path, content):
                    async with semaphore:
                        # Minimal delay for rate limit safety
                        await asyncio.sleep(3.0)

                        # [COST-SAVING] Truncate large files before sending to LLM
                        truncated_content = Tokenizer.truncate(content, 2000)

                        await self._broadcast_progress(
                            project_id,
                            idx + 1,
                            total_files,
                            file_path,
                            f"Analyzing: {file_path}",
                        )
                        return await miner.analyze_file(file_path, truncated_content)

                tasks = [analyze_with_limit(i, f[0], f[1]) for i, f in enumerate(files)]

                # Run all tasks
                results = await asyncio.gather(*tasks)

                # Filter None results and format
                for res in results:
                    if res:
                        miner_results.append(res.model_dump())

                miner_output = {"results": miner_results}
                logger.info(
                    f"[Service] Miner completed. Analyzed {len(miner_results)} files."
                )

                # Save miner output
                await self._save_json(miner_output_file, miner_output)

            # ============== PHASE 2: ARCHITECT ==============
            navigation_file = project_output_path / "navigation.json"
            navigation = None

            # [COST-SAVING] Check if navigation exists (Cache)
            if navigation_file.exists():
                logger.info(
                    f"[Service] Loading existing navigation from {navigation_file}"
                )
                await self._broadcast_stage(
                    project_id, "planning", "Loading cached documentation structure..."
                )
                async with aiofiles.open(navigation_file, "r", encoding="utf-8") as f:
                    content = await f.read()
                    navigation = json.loads(content)  # Use dict directly

                    # Broadcast the plan so frontend knows intended structure
                    await manager.broadcast(
                        project_id,
                        {
                            "type": "plan_generated",
                            "plan": {"tree": navigation["tree"]},
                        },
                    )
            else:
                await self._broadcast_stage(
                    project_id, "planning", "Designing documentation structure..."
                )

                architect = ArchitectAgent(client, on_event=event_handler)
                # Architect expects the dict output from miner
                nav_obj = await architect.plan_navigation(miner_output)

                if not nav_obj:
                    await self._broadcast_stage(
                        project_id,
                        "error",
                        "Failed to generate documentation structure",
                    )
                    return {"status": "error", "message": "Architect failed"}

                # Broadcast the generated plan
                await manager.broadcast(
                    project_id,
                    {
                        "type": "plan_generated",
                        "plan": {"tree": [item.model_dump() for item in nav_obj.tree]},
                    },
                )

                navigation = nav_obj.model_dump()

                # Save navigation
                await self._save_json(navigation_file, navigation)

                logger.info(
                    f"[Service] Architect completed. Navigation has {len(nav_obj.tree)} top-level items."
                )

            # ============== PHASE 3: SCRIBE ==============
            await self._broadcast_stage(
                project_id, "writing", "Writing documentation pages..."
            )

            scribe = ScribeAgent(client, on_event=event_handler)
            pages_dir = project_output_path / "pages"
            pages_dir.mkdir(exist_ok=True)

            # Use helper to extract pages from the dict structure (which handles both new and cached plans)
            tree_data = (
                navigation["tree"]
                if isinstance(navigation, dict)
                else [item.model_dump() for item in navigation.tree]
            )
            all_pages = self._get_all_pages_from_dict(tree_data)

            pages_generated = 0

            for idx, page_info in enumerate(all_pages):
                page_id = page_info["id"]
                page_title = page_info["label"]
                target_modules = page_info["modules"]

                # Check if page already exists to skip writing if needed?
                # For now let's overwrite pages to allow content updates, or we could add another cache check here.
                # User complaining about cost suggests we should probably skip existing pages too unless forced.
                # But Scribe is less expensive than Miner. Let's overwrite for correctness.

                await self._broadcast_progress(
                    project_id,
                    idx + 1,
                    len(all_pages),
                    page_title,
                    f"Writing: {page_title}",
                )

                # Determine page type
                page_type = (
                    "architecture_overview" if "overview" in page_id.lower() else "page"
                )

                try:
                    page_content = await scribe.write_page(
                        page_id=page_id,
                        page_type=page_type,
                        page_title=page_title,
                        target_modules=target_modules,
                        miner_output=miner_output,
                    )

                    if page_content:
                        # Save page as JSON with full metadata
                        page_filename = f"{page_id}.json"

                        # Convert WikiPageDetail to dict
                        page_data = page_content.model_dump()

                        # Add metadata if missing or fix inconsistencies
                        if not page_data.get("id"):
                            page_data["id"] = page_id

                        # Ensure content_markdown is populated
                        if not page_data.get("content_markdown"):
                            page_data["content_markdown"] = "# Content not generated."

                        async with aiofiles.open(
                            pages_dir / page_filename, "w", encoding="utf-8"
                        ) as f:
                            await f.write(json.dumps(page_data, indent=2))

                        pages_generated += 1
                        # Rate limit to be nice
                        await asyncio.sleep(0.5)

                except Exception as e:
                    logger.error(f"Failed to write page {page_id}: {e}")
                    # Continue with other pages

            await self._broadcast_stage(
                project_id,
                "completed",
                f"Documentation generated! {pages_generated} pages created.",
            )

            logger.info(
                f"[Service] Documentation pipeline completed. Output: {project_output_path}"
            )

            return {
                "status": "completed",
                "project_id": project_id,
                "output_path": str(project_output_path),
                "pages_generated": pages_generated,
            }

        except Exception as e:
            logger.error(f"[Service] Error: {e}")
            await self._broadcast_stage(project_id, "error", str(e))
            raise e

    async def _collect_source_files(self, repo_path: str) -> List[tuple]:
        """
        Collects source files from the repository using async file reading.
        """
        files = []
        repo = Path(repo_path)

        # Use simple os.walk first to completely prune SKIP_DIRS from traversal
        # This is much safer than rglob for huge directories like node_modules
        for root, dirs, filenames in os.walk(repo_path):
            # Prune skipped directories in-place
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]

            for filename in filenames:
                file_path = Path(root) / filename

                # Check extension blacklist
                if file_path.suffix.lower() in IGNORE_EXTENSIONS:
                    continue

                # Double check for hidden files
                if filename.startswith("."):
                    continue

                try:
                    # Use aiofiles for non-blocking I/O
                    async with aiofiles.open(
                        file_path, "r", encoding="utf-8", errors="ignore"
                    ) as f:
                        content = await f.read()

                    # Check for null bytes (binary file)
                    if "\0" in content:
                        continue

                    # Skip very large files (> 50KB) - Costs protection
                    if len(content) > 50000:
                        continue

                    relative_path = str(file_path.relative_to(repo))
                    files.append((relative_path, content))

                    # [COST-SAVING] HARD LIMIT for safety if things go wrong again
                    if len(files) > 200:
                        logger.warning(
                            "Reached safety limit of 200 files. Stopping collection to save costs."
                        )
                        return files

                except Exception as e:
                    logger.warning(f"Could not read {file_path}: {e}")

        return files

    def _get_all_pages_from_dict(
        self, items: List[Dict], parent_modules=None
    ) -> List[Dict]:
        """Recursive helper for dict-based navigation tree (used when loading cached plan)."""
        if parent_modules is None:
            parent_modules = []
        pages = []
        for item in items:
            node_type = item.get("type")
            node_id = item.get("id")
            node_label = item.get("label")
            children = item.get("children", [])

            if node_type == "page":
                pages.append(
                    {
                        "id": node_id,
                        "label": node_label,
                        "modules": parent_modules + ([node_id] if node_id else []),
                    }
                )

            if children:
                child_modules = parent_modules + ([node_id] if node_id else [])
                pages.extend(self._get_all_pages_from_dict(children, child_modules))
        return pages

    async def _save_json(self, path: Path, data: Dict[str, Any]):
        """Saves data to a JSON file"""
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, indent=2))

    async def _broadcast_stage(self, project_id: str, stage: str, message: str):
        """Helper to broadcast pipeline stage updates."""
        await manager.broadcast(
            project_id, {"type": "pipeline_stage", "stage": stage, "message": message}
        )

    async def _broadcast_progress(
        self, project_id: str, current: int, total: int, label: str, message: str
    ):
        """Helper to broadcast progress updates."""
        await manager.broadcast(
            project_id,
            {
                "type": "pipeline_progress",
                "current": current,
                "total": total,
                "page_label": label,
                "message": message,
            },
        )

    def _create_event_handler(self, project_id: str):
        """Creates an event handler for agent callbacks."""

        async def on_event(event: Dict[str, Any]):
            # AgentExecutor emits a full event dictionary
            if event.get("type") == "agent_thought":
                # Ensure it has an ID and timestamp
                if "id" not in event:
                    event["id"] = str(uuid.uuid4())
                if "timestamp" not in event:
                    event["timestamp"] = asyncio.get_event_loop().time()
                await manager.broadcast(project_id, event)
            else:
                # If for some reason we get something else
                # Fallback broadcast
                await manager.broadcast(
                    project_id,
                    {"type": "agent_thought", "subtype": "unknown", "data": event},
                )

        return on_event


# Global instance
documentation_service = DocumentationService()
