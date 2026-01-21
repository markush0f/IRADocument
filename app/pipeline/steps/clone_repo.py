from git import Repo
from app.infra.git_client import GitClient


class CloneRepositoryError(Exception):
    pass


def clone_repo(context) -> None:

    repo_url = context.repo_url
    repo_path = context.repo_path
    branch = getattr(context, "branch", None)

    git_client = GitClient()

    try:
        repo: Repo = git_client.clone_repository(
            repo_url=repo_url,
            dest_path=str(repo_path),
            branch=branch,
            depth=1,
        )
    except Exception as exc:
        raise CloneRepositoryError(f"Failed to clone repository {repo_url}") from exc

    context.repo = repo

    try:
        context.latest_commit = git_client.latest_commit(str(repo_path))
    except Exception:
        context.latest_commit = None
