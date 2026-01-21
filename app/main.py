from types import SimpleNamespace

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.pipeline.steps.clone_repo import CloneRepositoryError, clone_repo
from app.pipeline.steps.prepare_workspace import WorkspaceError, prepare_workspace

app = FastAPI(title="IRADocument API")


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
