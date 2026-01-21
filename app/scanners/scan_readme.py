"""README scanner that searches a repo recursively."""

from pathlib import Path


def scan_readme(repo_path: Path) -> dict:
    """Scan for README files under repo_path and return metadata."""
    readmes: list[dict[str, object]] = []

    for path in repo_path.rglob("*"):
        if not path.is_file():
            continue

        if not path.name.upper().startswith("README"):
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        if not content.strip():
            continue

        first_line = content.strip().splitlines()[0]

        readmes.append(
            {
                "path": str(path.relative_to(repo_path)),
                "filename": path.name,
                "extension": path.suffix.lower(),
                "size_bytes": path.stat().st_size,
                "title": first_line,
            }
        )

    return {
        "has_readme": bool(readmes),
        "readmes": readmes,
    }
