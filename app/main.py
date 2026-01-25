from contextlib import asynccontextmanager
from types import SimpleNamespace

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import SQLModel

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
