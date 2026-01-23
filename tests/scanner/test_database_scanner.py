from pathlib import Path

from app.core.config import settings
from app.core.logger import get_logger
from app.scanners.technologies.database import DatabaseScanner


def test_database_scanner_detects_files(tmp_path):
    settings.log_dir = str(tmp_path / "logs")
    logger = get_logger(f"test_db_scanner_{tmp_path.name}")

    # Use persistent fixture
    repo_path = Path("tests/fixtures/repo_with_databases")

    result = DatabaseScanner(repo_path).scan()

    logger.info("DatabaseScanner result: %s", result)

    assert result is not None
    assert result["type"] == "infrastructure"
    assert result["name"] == "database"

    assert result["binary_files"]["detected"] is True
    assert result["binary_files"]["count"] == 1
    files = [Path(p).name for p in result["binary_files"]["files"]]
    assert "data.sqlite3" in files

    assert result["scripts"]["detected"] is True
    # schema.sql + migrations/001.sql + seeds/users.sql
    assert result["scripts"]["count"] >= 3
    scripts = [Path(p).name for p in result["scripts"]["files"]]
    assert "schema.sql" in scripts
    assert "001_initial.sql" in scripts

    assert result["configs"]["detected"] is True
    assert result["configs"]["count"] == 1
    configs = [Path(p).name for p in result["configs"]["files"]]
    assert "alembic.ini" in configs

    assert result["directories"]["detected"] is True
    assert result["directories"]["count"] >= 2
    dirs = [Path(p).name for p in result["directories"]["paths"]]
    assert "migrations" in dirs
    assert "seeds" in dirs


def test_database_scanner_returns_none_clean_repo(tmp_path):
    settings.log_dir = str(tmp_path / "logs")
    logger = get_logger(f"test_db_scanner_none_{tmp_path.name}")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").touch()

    result = DatabaseScanner(tmp_path).scan()

    logger.info("DatabaseScanner result (no db): %s", result)

    assert result is None
