import os
import asyncio
from typing import List, Optional
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.models.endpoint import Endpoint
from app.agents.core.factory import LLMFactory
from app.agents.agent_executor import AgentExecutor

logger = get_logger(__name__)

from app.agents.extractor.prompts import (
    ENDPOINT_EXTRACTION_PROMPT,
    FILE_SELECTION_PROMPT,
)


class EndpointService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.llm_client = LLMFactory.get_client(provider="openai", model="gpt-4o-mini")

    async def extract_and_save_endpoints(
        self, project_id: str, root_path: str
    ) -> List[Endpoint]:
        """
        Scans the project for endpoints using AI and saves them to DB.
        """
        logger.info(f"Starting endpoint extraction for project {project_id}")

        # 1. Collect ALL files first (very cheap)
        all_files = self._collect_all_files(root_path)
        logger.info(f"Walking tree found {len(all_files)} files.")

        # 2. Let AI pick candidates from the list
        candidate_files = await self._select_candidate_files_with_ai(
            root_path, all_files
        )
        logger.info(f"AI selected {len(candidate_files)} candidate files for analysis.")

        all_endpoints = []

        # 3. Analyze each candidate file
        BATCH_SIZE = 5
        for i in range(0, len(candidate_files), BATCH_SIZE):
            batch = candidate_files[i : i + BATCH_SIZE]
            tasks = [self._analyze_file(project_id, root_path, f) for f in batch]
            results = await asyncio.gather(*tasks)

            for res in results:
                if res:
                    all_endpoints.extend(res)

            await asyncio.sleep(1)  # Rate limit protection

        return all_endpoints

    def _collect_all_files(self, root_path: str) -> List[str]:
        """Collects every single file path in the project."""
        candidates = []
        full_root_path = os.path.abspath(root_path)
        for root, dirs, files in os.walk(full_root_path):
            for file in files:
                candidates.append(os.path.join(root, file))
        return candidates

    async def _select_candidate_files_with_ai(
        self, root_path: str, file_paths: List[str]
    ) -> List[str]:
        """Uses AI to pick which files are worth scanning."""
        try:
            rel_paths = [os.path.relpath(p, root_path) for p in file_paths]
            # Join paths into a block (truncate if too long, though file lists are usually fine)
            file_list_str = "\n".join(rel_paths)

            executor = AgentExecutor(self.llm_client)
            executor.set_system_prompt(FILE_SELECTION_PROMPT)
            executor.add_user_message(f"File List:\n{file_list_str}")

            tool_def = {
                "type": "function",
                "function": {
                    "name": "submit_selected_files",
                    "description": "Submit list of files that likely contain endpoints",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "selected_files": {
                                "type": "array",
                                "items": {"type": "string"},
                            }
                        },
                        "required": ["selected_files"],
                    },
                },
            }

            selection = {"files": []}

            def submit_selected_files(selected_files):
                selection["files"] = selected_files
                return "Selection received"

            executor.register_tool(tool_def, submit_selected_files)

            await executor.run_until_complete(max_iterations=1)

            # Map back to absolute paths
            chosen_rel = selection["files"]
            return [os.path.join(root_path, p) for p in chosen_rel]

        except Exception as e:
            logger.error(f"AI File Selection failed: {e}")
            # Fallback: if AI fails, we might want to return a small heuristic sample
            # or just return everything if it's small. For now, empty or basic heuristic.
            return []

    async def _analyze_file(
        self, project_id: str, root_path: str, file_path: str
    ) -> List[Endpoint]:
        """
        Uses LLM to extract endpoints from a single file.
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if len(content) > 20000:
                logger.warning(f"Skipping {file_path} (too large)")
                return []

            executor = AgentExecutor(self.llm_client)
            executor.set_system_prompt(ENDPOINT_EXTRACTION_PROMPT)

            rel_path = os.path.relpath(file_path, root_path)

            msg = f"File: {rel_path}\nCode:\n```{content}```"
            executor.add_user_message(msg)

            # Tool definition
            tool_def = {
                "type": "function",
                "function": {
                    "name": "submit_endpoints",
                    "description": "Submit list of found endpoints",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "endpoints": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "method": {
                                            "type": "string",
                                            "enum": [
                                                "GET",
                                                "POST",
                                                "PUT",
                                                "DELETE",
                                                "PATCH",
                                                "OPTIONS",
                                                "HEAD",
                                            ],
                                        },
                                        "path": {"type": "string"},
                                        "description": {"type": "string"},
                                        "line_number": {"type": "integer"},
                                    },
                                    "required": ["method", "path"],
                                },
                            }
                        },
                        "required": ["endpoints"],
                    },
                },
            }

            extracted_data = {"items": []}

            def submit_endpoints(endpoints):
                extracted_data["items"] = endpoints
                return "Saved"

            executor.register_tool(tool_def, submit_endpoints)

            await executor.run_until_complete(max_iterations=1)

            new_endpoints = []
            for item in extracted_data["items"]:
                # Save to DB
                endpoint = Endpoint(
                    project_id=project_id,
                    path=item.get("path"),
                    method=item.get("method"),
                    file_path=rel_path,
                    line_number=item.get("line_number"),
                    description=item.get("description"),
                    framework="detected",
                )
                self.session.add(endpoint)
                new_endpoints.append(endpoint)

            await self.session.commit()
            return new_endpoints

        except Exception as e:
            logger.error(f"Error extracting endpoints from {file_path}: {e}")
            return []

    async def get_project_endpoints(self, project_id: str) -> List[Endpoint]:
        statement = select(Endpoint).where(Endpoint.project_id == project_id)
        result = await self.session.execute(statement)
        return result.scalars().all()
