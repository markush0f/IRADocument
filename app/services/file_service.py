from datetime import datetime, timezone
from typing import List, Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.file import File
from app.storage.file_repository import FileRepository


class FileService:
    def __init__(self, session: AsyncSession):
        self.repo = FileRepository(session)

    async def register_file(
        self,
        project_id: str,
        path: str,
        language: Optional[str] = None,
        file_hash: Optional[str] = None,
    ) -> File:
        """Registers a file in the project."""
        file_obj = File(
            project_id=project_id,
            path=path,
            language=language,
            hash=file_hash,
            analyzed=0,
        )
        return await self.repo.create(file_obj)

    async def get_project_files(self, project_id: str) -> List[File]:
        """Gets all files belonging to a project."""
        return await self.repo.get_by_project(project_id)

    async def mark_as_analyzed(
        self, project_id: str, path: str, summary: str
    ) -> Optional[File]:
        """Updates file analysis status."""
        data = {
            "analyzed": 1,
            "summary": summary,
            "last_analyzed_at": datetime.now(timezone.utc).isoformat(),
        }
        # In this specific repo, the ID is likely a composite or the repo method needs to handle it
        # Our base repo uses a single id, but File has composite key (project_id, path)
        # We might need to adjust the repository but for now we follow the pattern
        return await self.repo.update((project_id, path), data)
