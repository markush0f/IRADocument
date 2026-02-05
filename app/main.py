from contextlib import asynccontextmanager
from types import SimpleNamespace
from enum import Enum
from typing import List, Optional
import json

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import SQLModel

from app.agents.tools import registry  # Import registry and triggers tool registration
from app.core.database import engine
from app.models import (
    Project,
    File,
    Fact,
    Relation,
)  # Import all models to register them
from app.pipeline.steps.clone_repo import CloneRepositoryError, clone_repo
from app.pipeline.steps.prepare_workspace import WorkspaceError, prepare_workspace


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Export Tool Definitions to JSON for visibility/external use
    registry.save_to_json("app/agents/tools/definitions.json")

    yield


app = FastAPI(title="IRADocument API", lifespan=lifespan)


class CloneRepoRequest(BaseModel):
    repo_url: str = Field(..., min_length=1)
    branch: str | None = None


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "IRADocument API is running"}


@app.post("/clone")
def clone_project(payload: CloneRepoRequest) -> dict[str, object]:
    context = SimpleNamespace(repo_url=payload.repo_url, branch=payload.branch)
    try:
        prepare_workspace(context)
        clone_repo(context)
    except (WorkspaceError, CloneRepositoryError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "workspace_id": context.workspace_id,
        "repo_path": str(context.repo_path),
        "latest_commit": context.latest_commit,
    }


class AnalysisStage(str, Enum):
    exploration = "exploration"
    tech_stack = "tech_stack"


class AnalysisRequest(BaseModel):
    stages: Optional[List[AnalysisStage]] = Field(
        default=None,
        description="List of stages to execute: 'exploration' and/or 'tech_stack'",
    )


@app.post("/analysis/tech-stack")
async def analyze_repo_tech_stack(payload: CloneRepoRequest):
    """
    Clones a repository and performs ONLY technical stack analysis.
    Directly returns the AI reasoning about the discovered stack.
    """
    from app.services.analysis_service import AnalysisService
    from app.services.project_service import ProjectService
    from app.core.database import AsyncSessionLocal

    # 1. Setup context and Clone
    context = SimpleNamespace(repo_url=payload.repo_url, branch=payload.branch)
    try:
        prepare_workspace(context)
        clone_repo(context)
    except (WorkspaceError, CloneRepositoryError) as exc:
        raise HTTPException(status_code=500, detail=f"Clone failed: {str(exc)}")

    project_id = context.workspace_id
    repo_path = str(context.repo_path)

    async with AsyncSessionLocal() as session:
        # 2. Ensure project is registered
        project_service = ProjectService(session)
        try:
            await project_service.create_project(
                id=project_id, name=f"Quick Tech Scan {project_id}", root_path=repo_path
            )
        except Exception:
            # Continue if already exists
            pass

        # 3. Run ONLY tech_stack analysis
        analysis_service = AnalysisService(session)
        result = await analysis_service.generate_analysis_report(
            project_id, enabled_stages=["tech_stack"]
        )

        if result.get("status") == "failed":
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result


@app.post("/pipeline/analyze")
async def run_full_pipeline(payload: CloneRepoRequest):
    from app.pipeline.orchestrator import create_standard_pipeline, PipelineContext
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        # 1. Initialize Context
        context = PipelineContext(
            repo_url=payload.repo_url, branch=payload.branch, session=session
        )

        # 2. Run the Parent Pipeline (Orchestrator)
        pipeline = create_standard_pipeline()
        await pipeline.run(context)

        if context.errors:
            raise HTTPException(status_code=500, detail={"errors": context.errors})

        # 3. Return the result
        report_payload = {}
        if context.discovery_report:
            report_payload = (
                json.loads(context.discovery_report.payload)
                if isinstance(context.discovery_report.payload, str)
                else context.discovery_report.payload
            )

        return {
            "workspace_id": context.workspace_id,
            "status": "completed",
            "analysis": context.analysis_result,
            "documentation": report_payload,
            "repo_details": {
                "latest_commit": context.latest_commit,
                "repo_path": str(context.repo_path),
            },
        }


@app.post("/documentation/generate")
async def generate_wiki(payload: CloneRepoRequest):
    """
    Clones a repository and generates full wiki documentation (Miner -> Architect -> Scribe).
    """
    from app.services.documentation_service import DocumentationService

    # 1. Setup context and Clone
    context = SimpleNamespace(repo_url=payload.repo_url, branch=payload.branch)
    try:
        prepare_workspace(context)
        clone_repo(context)
    except (WorkspaceError, CloneRepositoryError) as exc:
        raise HTTPException(status_code=500, detail=f"Clone failed: {str(exc)}")

    project_id = context.workspace_id
    repo_path = str(context.repo_path)

    # 2. Run Documentation Pipeline
    doc_service = DocumentationService()
    result = await doc_service.generate_documentation(
        project_id=project_id, root_path=repo_path
    )

    if result.get("status") == "failed":
        raise HTTPException(status_code=500, detail=result.get("error"))

    return result


@app.post("/analysis/endpoints")
async def extract_endpoints(payload: CloneRepoRequest):
    """
    Clones a repo and extracts API endpoints using AI.
    """
    from app.services.endpoint_service import EndpointService
    from app.core.database import AsyncSessionLocal

    # 1. Clone
    context = SimpleNamespace(repo_url=payload.repo_url, branch=payload.branch)
    try:
        prepare_workspace(context)
        clone_repo(context)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Clone failed: {str(exc)}")

    project_id = context.workspace_id
    repo_path = str(context.repo_path)

    # 2. Extract
    async with AsyncSessionLocal() as session:
        service = EndpointService(session)
        endpoints = await service.extract_and_save_endpoints(project_id, repo_path)

        return {
            "project_id": project_id,
            "count": len(endpoints),
            "endpoints": endpoints,
        }
