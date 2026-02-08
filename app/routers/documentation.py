import os
import asyncio
from types import SimpleNamespace
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from app.services.documentation_service import documentation_service
from app.core.logger import get_logger
from app.pipeline.steps.prepare_workspace import prepare_workspace, WorkspaceError
from app.pipeline.steps.clone_repo import clone_repo, CloneRepositoryError

logger = get_logger(__name__)

router = APIRouter()


class DocumentationRequest(BaseModel):
    project_id: Optional[str] = None
    repo_url: Optional[str] = None
    repo_path: Optional[str] = None
    branch: str = "main"
    provider: str = "openai"
    model: Optional[str] = "gpt-4o-mini"  # or ollama/llama2


class DocumentationResponse(BaseModel):
    status: str
    project_id: str
    message: str


@router.post("/documentation/generate", response_model=DocumentationResponse)
async def generate_documentation(
    request: DocumentationRequest, background_tasks: BackgroundTasks
):
    """
    Endpoint to trigger documentation generation.
    Supports either a local path (repo_path) or a remote URL (repo_url).
    """
    project_id = request.project_id
    repo_path = request.repo_path

    # 1. Clone repository if needed
    if request.repo_url and not repo_path:
        # Generate a project ID if not provided
        if not project_id:
            import uuid

            project_id = str(uuid.uuid4())

        try:
            # Prepare context for cloning tool
            context = SimpleNamespace(
                repo_url=request.repo_url,
                branch=request.branch,
                workspace_id=project_id,  # Ensure workspace match
            )
            # This prepares /tmp/ira-docgen/{project_id}/repo
            prepare_workspace(context)
            clone_repo(context)
            repo_path = str(context.repo_path)
            logger.info(f"Cloned repository to: {repo_path}")
        except Exception as e:
            logger.error(f"Clone failed: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to clone repository: {str(e)}"
            )

    # If project_id is still missing (local path case)
    if not project_id and repo_path:
        project_id = os.path.basename(os.path.normpath(repo_path))

    if not project_id:
        project_id = "default-project"

    # 2. Validate repository path
    if not repo_path or not os.path.isdir(repo_path):
        raise HTTPException(
            status_code=400, detail=f"Repository path not found: {repo_path}"
        )

    # 3. Start pipeline in background
    # We use asyncio.create_task to ensure it runs independently of the request scope
    # properly within the async loop. BackgroundTasks is standard FastAPI.
    background_tasks.add_task(
        documentation_service.generate_documentation,
        project_id=project_id,
        repo_path=repo_path,
        provider=request.provider,
        model=request.model,
    )

    return DocumentationResponse(
        status="started",
        project_id=project_id,
        message="Documentation generation started in background.",
    )
