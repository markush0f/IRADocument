from __future__ import annotations

import os
from typing import Any

import httpx
from git import GitCommandError, InvalidGitRepositoryError, NoSuchPathError, Repo


class GitClient:
    def __init__(
        self,
        github_token: str | None = None,
        api_base_url: str = "https://api.github.com",
        timeout: float = 30.0,
    ) -> None:
        self._github_token = github_token or os.getenv("GITHUB_TOKEN")
        self._api_base_url = api_base_url.rstrip("/")
        self._timeout = timeout

    def clone_repository(
        self,
        repo_url: str,
        dest_path: str,
        branch: str | None = None,
        depth: int | None = None,
    ) -> Repo:
        clone_kwargs: dict[str, Any] = {}
        if branch:
            clone_kwargs["branch"] = branch
        if depth:
            clone_kwargs["depth"] = depth
            clone_kwargs["single_branch"] = True
        try:
            return Repo.clone_from(repo_url, dest_path, **clone_kwargs)
        except GitCommandError as exc:
            raise RuntimeError(f"Failed to clone repository {repo_url}: {exc}") from exc

    def open_repository(self, repo_path: str) -> Repo:
        try:
            return Repo(repo_path)
        except (InvalidGitRepositoryError, NoSuchPathError, GitCommandError) as exc:
            raise RuntimeError(f"Invalid repository at {repo_path}: {exc}") from exc

    def list_local_branches(self, repo_path: str) -> list[str]:
        repo = self.open_repository(repo_path)
        return [branch.name for branch in repo.branches]

    def checkout_branch(
        self,
        repo_path: str,
        branch_name: str,
        create: bool = False,
        start_point: str | None = None,
    ) -> None:
        repo = self.open_repository(repo_path)
        try:
            if create:
                if start_point:
                    repo.git.checkout("-b", branch_name, start_point)
                else:
                    repo.git.checkout("-b", branch_name)
            else:
                repo.git.checkout(branch_name)
        except GitCommandError as exc:
            raise RuntimeError(
                f"Failed to checkout branch {branch_name}: {exc}"
            ) from exc

    def pull(
        self, repo_path: str, remote_name: str = "origin", branch: str | None = None
    ) -> None:
        repo = self.open_repository(repo_path)
        try:
            remote = repo.remotes[remote_name]
            if branch:
                remote.pull(branch)
            else:
                remote.pull()
        except (GitCommandError, IndexError) as exc:
            raise RuntimeError(f"Failed to pull from {remote_name}: {exc}") from exc

    def latest_commit(self, repo_path: str) -> dict[str, Any]:
        repo = self.open_repository(repo_path)
        commit = repo.head.commit
        return {
            "hexsha": commit.hexsha,
            "author": commit.author.name,
            "email": commit.author.email,
            "message": commit.message.strip(),
            "authored_datetime": commit.authored_datetime.isoformat(),
        }

    def get_github_repo(self, owner: str, repo: str) -> dict[str, Any]:
        return self._request_json("GET", f"/repos/{owner}/{repo}")

    def list_github_repo_branches(self, owner: str, repo: str) -> list[str]:
        data = self._request_json("GET", f"/repos/{owner}/{repo}/branches")
        return [item["name"] for item in data]

    def _request_json(
        self, method: str, path: str, params: dict[str, Any] | None = None
    ) -> Any:
        url = f"{self._api_base_url}{path}"
        headers = {"Accept": "application/vnd.github+json"}
        if self._github_token:
            headers["Authorization"] = f"Bearer {self._github_token}"
        with httpx.Client(timeout=self._timeout) as client:
            response = client.request(method, url, headers=headers, params=params)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"GitHub API error: {exc.response.status_code} {exc.response.text}"
            ) from exc
        return response.json()
