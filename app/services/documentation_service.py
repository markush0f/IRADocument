import os
import json
import asyncio
import uuid
import time
import aiofiles
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.agents.core.factory import LLMFactory
from app.agents.miner.agent import MinerAgent
from app.agents.architect.agent import ArchitectAgent
from app.agents.scribe.agent import ScribeAgent
from app.core.logger import get_logger
from app.core.socket_manager import manager
from app.core.tokenizer import Tokenizer
from app.core.constants import (
    SKIP_DIRS,
    IGNORE_EXTENSIONS,
    IGNORE_FILENAMES,
    MAX_FILE_SIZE_BYTES,
    MAX_FILES_LIMIT,
    COST_PER_MILLION_INPUT_TOKENS,
    COST_PER_MILLION_OUTPUT_TOKENS,
    DEFAULT_MAX_COST_USD,
    MINER_CONCURRENCY_LIMIT,
    MINER_RATE_DELAY_SECONDS,
    MINER_MAX_TOKENS_PER_FILE,
    SCRIBE_MAX_INPUT_TOKENS,
)

logger = get_logger(__name__)


class DocumentationService:
    """
    Orchestrates the AI Documentation Pipeline (Miner -> Architect -> Scribe).

    This service manages the full lifecycle of documentation generation with:
    - Per-model cost estimation and safety limits.
    - Concurrency and rate-limit protection.
    - Multi-phase caching (Miner output, Navigation, and individual Scribe pages).
    - Real-time progress broadcasting via WebSocket.
    """

    def __init__(self):
        self.output_dir = Path("output/docs")

    # ==================== PUBLIC API ====================

    async def generate_documentation(
        self,
        project_id: str,
        repo_path: str,
        provider: str = "openai",
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes the full Triad pipeline (Miner -> Architect -> Scribe).

        Args:
            project_id: Unique identifier for the project session.
            repo_path: Local filesystem path to the repository root.
            provider: LLM provider id (openai, gemini, ollama).
            model: Specific model name (e.g., gpt-4o-mini, gemini-1.5-flash).

        Returns:
            Dict containing status, output path, statistics, and cost report.
        """
        pipeline_start = time.time()
        cost_tracker = {"input_tokens": 0, "output_tokens_est": 0, "phases": {}}

        logger.info(
            f"[Pipeline] Starting documentation for project={project_id}, "
            f"provider={provider}, model={model}"
        )

        try:
            await self._broadcast_stage(
                project_id, "started", "Initializing documentation pipeline..."
            )

            project_output_path = self.output_dir / project_id
            project_output_path.mkdir(parents=True, exist_ok=True)

            client = LLMFactory.get_client(provider=provider, model=model)
            event_handler = self._create_event_handler(project_id)

            resolved_model = model or self._resolve_default_model(provider)

            # Configure tokenizer for accurate counting with this provider/model
            Tokenizer.configure(provider, resolved_model)

            # ============== PHASE 1: MINER ==============
            miner_output, miner_cost = await self._run_miner_phase(
                project_id=project_id,
                repo_path=repo_path,
                output_path=project_output_path,
                client=client,
                event_handler=event_handler,
                model_name=resolved_model,
                provider=provider,
            )

            if miner_output is None:
                return {"status": "error", "message": "Miner phase failed"}

            cost_tracker["phases"]["miner"] = miner_cost

            # ============== PHASE 2: ARCHITECT ==============
            navigation, architect_cost = await self._run_architect_phase(
                project_id=project_id,
                output_path=project_output_path,
                client=client,
                event_handler=event_handler,
                miner_output=miner_output,
            )

            if navigation is None:
                return {"status": "error", "message": "Architect phase failed"}

            cost_tracker["phases"]["architect"] = architect_cost

            # ============== PHASE 3: SCRIBE ==============
            pages_generated, scribe_cost = await self._run_scribe_phase(
                project_id=project_id,
                output_path=project_output_path,
                client=client,
                event_handler=event_handler,
                navigation=navigation,
                miner_output=miner_output,
            )

            cost_tracker["phases"]["scribe"] = scribe_cost

            # ============== COMPLETE ==============
            elapsed = time.time() - pipeline_start
            total_cost = sum(
                phase.get("estimated_cost_usd", 0)
                for phase in cost_tracker["phases"].values()
            )

            await self._broadcast_stage(
                project_id,
                "completed",
                f"Documentation generated! {pages_generated} pages in {elapsed:.1f}s. "
                f"Estimated cost: ${total_cost:.4f}",
            )

            logger.info(
                f"[Pipeline] Completed in {elapsed:.1f}s. "
                f"Pages: {pages_generated}, Est. cost: ${total_cost:.4f}"
            )

            return {
                "status": "completed",
                "project_id": project_id,
                "output_path": str(project_output_path),
                "pages_generated": pages_generated,
                "elapsed_seconds": round(elapsed, 2),
                "cost_report": cost_tracker,
            }

        except Exception as e:
            logger.error(f"[Pipeline] Fatal error: {e}", exc_info=True)
            await self._broadcast_stage(project_id, "error", str(e))
            raise

    # ==================== PHASE 1: MINER ====================

    async def _run_miner_phase(
        self,
        project_id: str,
        repo_path: str,
        output_path: Path,
        client,
        event_handler,
        model_name: str,
        provider: str,
    ) -> tuple:
        """
        Runs the Miner phase: collect files, estimate cost, analyze with LLM.
        Returns (miner_output_dict, cost_info_dict).
        """
        miner_output_file = output_path / "miner_output.json"
        cost_info = {"estimated_cost_usd": 0, "cached": False}

        # Check cache
        if miner_output_file.exists():
            logger.info(f"[Miner] Loading cached output from {miner_output_file}")
            await self._broadcast_stage(
                project_id, "mining", "Loading cached analysis (skipping mining)..."
            )
            miner_output = await self._load_json(miner_output_file)
            cost_info["cached"] = True
            return miner_output, cost_info

        await self._broadcast_stage(project_id, "mining", "Collecting source files...")

        # Collect files
        files = await self._collect_source_files(repo_path)
        logger.info(f"[Miner] Collected {len(files)} source files")

        if not files:
            await self._broadcast_stage(
                project_id, "error", "No source files found in repository"
            )
            return None, cost_info

        # Estimate cost
        total_tokens = sum(Tokenizer.count(content) for _, content in files)
        input_cost_rate = self._get_input_cost_rate(model_name, provider)
        output_cost_rate = self._get_output_cost_rate(model_name, provider)

        # Estimate: each file produces ~200 output tokens
        estimated_output_tokens = len(files) * 200
        estimated_input_cost = (total_tokens / 1_000_000) * input_cost_rate
        estimated_output_cost = (estimated_output_tokens / 1_000_000) * output_cost_rate
        estimated_total = estimated_input_cost + estimated_output_cost

        cost_info["input_tokens"] = total_tokens
        cost_info["estimated_output_tokens"] = estimated_output_tokens
        cost_info["estimated_cost_usd"] = round(estimated_total, 6)
        cost_info["model"] = model_name
        cost_info["files_count"] = len(files)

        logger.info(
            f"[Miner] Cost estimate: {total_tokens:,} input tokens, "
            f"~{estimated_output_tokens:,} output tokens, "
            f"${estimated_total:.4f} (rate: ${input_cost_rate}/M in, ${output_cost_rate}/M out)"
        )

        await self._broadcast_stage(
            project_id,
            "mining",
            f"Analyzing {len(files)} files (~{total_tokens:,} tokens, "
            f"est. ${estimated_total:.4f})...",
        )

        if estimated_total > DEFAULT_MAX_COST_USD:
            msg = (
                f"SAFETY LIMIT: Estimated cost ${estimated_total:.2f} "
                f"exceeds ${DEFAULT_MAX_COST_USD:.2f}. "
                f"Reduce files or use a cheaper model."
            )
            logger.error(f"[Miner] {msg}")
            await self._broadcast_stage(project_id, "error", msg)
            return None, cost_info

        # Run analysis with concurrency control
        miner = MinerAgent(client, on_event=event_handler)
        semaphore = asyncio.Semaphore(MINER_CONCURRENCY_LIMIT)
        total_files = len(files)

        async def analyze_with_limit(idx: int, file_path: str, content: str):
            async with semaphore:
                await asyncio.sleep(MINER_RATE_DELAY_SECONDS)

                truncated_content = Tokenizer.truncate(
                    content, MINER_MAX_TOKENS_PER_FILE
                )

                await self._broadcast_progress(
                    project_id,
                    idx + 1,
                    total_files,
                    file_path,
                    f"Mining: {file_path}",
                )
                return await miner.analyze_file(file_path, truncated_content)

        tasks = [
            analyze_with_limit(i, fpath, fcontent)
            for i, (fpath, fcontent) in enumerate(files)
        ]
        results = await asyncio.gather(*tasks)

        miner_results = [res.model_dump() for res in results if res is not None]
        miner_output = {"results": miner_results}

        logger.info(
            f"[Miner] Completed. Analyzed {len(miner_results)}/{total_files} files."
        )

        await self._save_json(miner_output_file, miner_output)
        return miner_output, cost_info

    # ==================== PHASE 2: ARCHITECT ====================

    async def _run_architect_phase(
        self,
        project_id: str,
        output_path: Path,
        client,
        event_handler,
        miner_output: Dict[str, Any],
    ) -> tuple:
        """
        Runs the Architect phase: plan navigation structure.
        Returns (navigation_dict, cost_info_dict).
        """
        navigation_file = output_path / "navigation.json"
        cost_info = {"estimated_cost_usd": 0, "cached": False}

        # Check cache
        if navigation_file.exists():
            logger.info(f"[Architect] Loading cached navigation from {navigation_file}")
            await self._broadcast_stage(
                project_id, "planning", "Loading cached documentation structure..."
            )
            navigation = await self._load_json(navigation_file)

            await manager.broadcast(
                project_id,
                {"type": "plan_generated", "plan": {"tree": navigation["tree"]}},
            )
            cost_info["cached"] = True
            return navigation, cost_info

        await self._broadcast_stage(
            project_id, "planning", "Designing documentation structure..."
        )

        architect = ArchitectAgent(client, on_event=event_handler)
        nav_obj = await architect.plan_navigation(miner_output)

        if not nav_obj:
            await self._broadcast_stage(
                project_id, "error", "Failed to generate documentation structure"
            )
            return None, cost_info

        await manager.broadcast(
            project_id,
            {
                "type": "plan_generated",
                "plan": {"tree": [item.model_dump() for item in nav_obj.tree]},
            },
        )

        navigation = nav_obj.model_dump()
        await self._save_json(navigation_file, navigation)

        logger.info(
            f"[Architect] Completed. Navigation has {len(nav_obj.tree)} top-level items."
        )

        return navigation, cost_info

    # ==================== PHASE 3: SCRIBE ====================

    async def _run_scribe_phase(
        self,
        project_id: str,
        output_path: Path,
        client,
        event_handler,
        navigation: Dict[str, Any],
        miner_output: Dict[str, Any],
    ) -> tuple:
        """
        Runs the Scribe phase: write documentation pages.
        Caches individual pages to avoid regenerating existing ones.
        Returns (pages_generated_count, cost_info_dict).
        """
        cost_info = {"estimated_cost_usd": 0, "pages_written": 0, "pages_cached": 0}

        await self._broadcast_stage(
            project_id, "writing", "Writing documentation pages..."
        )

        scribe = ScribeAgent(client, on_event=event_handler)
        pages_dir = output_path / "pages"
        pages_dir.mkdir(exist_ok=True)

        tree_data = (
            navigation["tree"]
            if isinstance(navigation, dict)
            else [item.model_dump() for item in navigation.tree]
        )
        all_pages = self._get_all_pages_from_dict(tree_data)

        pages_generated = 0
        pages_cached = 0

        for idx, page_info in enumerate(all_pages):
            page_id = page_info["id"]
            page_title = page_info["label"]
            target_modules = page_info["modules"]
            page_filename = f"{page_id}.json"
            page_file_path = pages_dir / page_filename

            # Cache check: skip pages that already exist
            if page_file_path.exists():
                logger.info(f"[Scribe] Skipping cached page: {page_id}")
                pages_cached += 1
                pages_generated += 1
                await self._broadcast_progress(
                    project_id,
                    idx + 1,
                    len(all_pages),
                    page_title,
                    f"Cached: {page_title}",
                )
                continue

            await self._broadcast_progress(
                project_id,
                idx + 1,
                len(all_pages),
                page_title,
                f"Writing: {page_title}",
            )

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
                    page_data = page_content.model_dump()

                    if not page_data.get("id"):
                        page_data["id"] = page_id

                    if not page_data.get("content_markdown"):
                        page_data["content_markdown"] = "# Content not generated."

                    async with aiofiles.open(
                        page_file_path, "w", encoding="utf-8"
                    ) as f:
                        await f.write(json.dumps(page_data, indent=2))

                    pages_generated += 1
                    await asyncio.sleep(0.3)

            except Exception as e:
                logger.error(f"[Scribe] Failed to write page {page_id}: {e}")

        cost_info["pages_written"] = pages_generated - pages_cached
        cost_info["pages_cached"] = pages_cached

        logger.info(
            f"[Scribe] Completed. Written: {pages_generated - pages_cached}, "
            f"Cached: {pages_cached}, Total: {pages_generated}"
        )

        return pages_generated, cost_info

    # ==================== FILE COLLECTION ====================

    async def _collect_source_files(self, repo_path: str) -> List[tuple]:
        """
        Collects source files from the repository.
        Uses pre-filtering by size and extension before reading content.
        Returns list of (relative_path, content) tuples.
        """
        files = []
        repo = Path(repo_path)
        skipped_stats = {
            "dirs": 0,
            "ext": 0,
            "hidden": 0,
            "size": 0,
            "binary": 0,
            "name": 0,
        }

        for root, dirs, filenames in os.walk(repo_path):
            # Prune directories in-place
            original_count = len(dirs)
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
            skipped_stats["dirs"] += original_count - len(dirs)

            for filename in filenames:
                file_path = Path(root) / filename

                # Skip by filename
                if filename in IGNORE_FILENAMES:
                    skipped_stats["name"] += 1
                    continue

                # Skip hidden files
                if filename.startswith("."):
                    skipped_stats["hidden"] += 1
                    continue

                # Skip by extension
                if file_path.suffix.lower() in IGNORE_EXTENSIONS:
                    skipped_stats["ext"] += 1
                    continue

                # Pre-filter by file size (avoids reading large files)
                try:
                    file_size = file_path.stat().st_size
                    if file_size > MAX_FILE_SIZE_BYTES:
                        skipped_stats["size"] += 1
                        continue
                    if file_size == 0:
                        continue
                except OSError:
                    continue

                try:
                    async with aiofiles.open(
                        file_path, "r", encoding="utf-8", errors="ignore"
                    ) as f:
                        content = await f.read()

                    # Check for null bytes (binary file detection)
                    if "\0" in content:
                        skipped_stats["binary"] += 1
                        continue

                    relative_path = str(file_path.relative_to(repo))
                    files.append((relative_path, content))

                    if len(files) >= MAX_FILES_LIMIT:
                        logger.warning(
                            f"[Collector] Reached file limit ({MAX_FILES_LIMIT}). "
                            f"Stopping collection."
                        )
                        break

                except Exception as e:
                    logger.warning(f"[Collector] Could not read {file_path}: {e}")

            if len(files) >= MAX_FILES_LIMIT:
                break

        logger.info(
            f"[Collector] Collected {len(files)} files. Skipped: "
            f"dirs={skipped_stats['dirs']}, ext={skipped_stats['ext']}, "
            f"hidden={skipped_stats['hidden']}, size={skipped_stats['size']}, "
            f"binary={skipped_stats['binary']}, name={skipped_stats['name']}"
        )

        return files

    # ==================== COST ESTIMATION ====================

    def _get_input_cost_rate(self, model_name: str, provider: str) -> float:
        """Returns cost per million input tokens for the given model."""
        if provider == "ollama":
            return 0.0
        return COST_PER_MILLION_INPUT_TOKENS.get(model_name, 0.50)

    def _get_output_cost_rate(self, model_name: str, provider: str) -> float:
        """Returns cost per million output tokens for the given model."""
        if provider == "ollama":
            return 0.0
        return COST_PER_MILLION_OUTPUT_TOKENS.get(model_name, 1.50)

    def _resolve_default_model(self, provider: str) -> str:
        """Resolves the default model name for a provider."""
        defaults = {
            "openai": "gpt-4o-mini",
            "gemini": "gemini-pro-latest",
            "ollama": "mistral:7b-instruct",
        }
        return defaults.get(provider, "unknown")

    # ==================== NAVIGATION HELPERS ====================

    def _get_all_pages_from_dict(
        self, items: List[Dict], parent_modules=None
    ) -> List[Dict]:
        """Recursively extracts all pages from a navigation tree dict."""
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

    # ==================== I/O HELPERS ====================

    async def _save_json(self, path: Path, data: Dict[str, Any]):
        """Saves data to a JSON file."""
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, indent=2))

    async def _load_json(self, path: Path) -> Dict[str, Any]:
        """Loads data from a JSON file."""
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            content = await f.read()
            return json.loads(content)

    # ==================== WEBSOCKET BROADCASTING ====================

    async def _broadcast_stage(self, project_id: str, stage: str, message: str):
        """Broadcasts pipeline stage updates to connected clients."""
        await manager.broadcast(
            project_id,
            {"type": "pipeline_stage", "stage": stage, "message": message},
        )

    async def _broadcast_progress(
        self, project_id: str, current: int, total: int, label: str, message: str
    ):
        """Broadcasts progress updates to connected clients."""
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
            if event.get("type") == "agent_thought":
                if "id" not in event:
                    event["id"] = str(uuid.uuid4())
                if "timestamp" not in event:
                    event["timestamp"] = asyncio.get_event_loop().time()
                await manager.broadcast(project_id, event)
            else:
                await manager.broadcast(
                    project_id,
                    {"type": "agent_thought", "subtype": "unknown", "data": event},
                )

        return on_event


# Global instance
documentation_service = DocumentationService()
