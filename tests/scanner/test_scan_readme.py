from pathlib import Path
from app.scanners.scan_readme import scan_readme


def test_scan_readmes_any_extension():
    repo_path = Path("tests/fixtures/repo_with_various_readmes")

    result = scan_readme(repo_path)

    paths = {r["path"] for r in result["readmes"]}

    assert "README.md" in paths
    assert "README.en.md" in paths
    assert "docs/README-backend.rst" in paths
