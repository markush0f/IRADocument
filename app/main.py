from contextlib import asynccontextmanager
from types import SimpleNamespace
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


@app.post("/analyze/{project_id}")
async def analyze_project(project_id: str):
    from app.services.analysis_service import AnalysisService
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        service = AnalysisService(session)
        result = await service.generate_analysis_report(project_id)
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
