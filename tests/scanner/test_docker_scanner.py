from pathlib import Path

from app.core.config import settings
from app.core.logger import get_logger
from app.scanners.technologies.docker import DockerScanner


def test_docker_scanner_detects_files(tmp_path):
    settings.log_dir = str(tmp_path / "logs")
    logger = get_logger(f"test_docker_scanner_{tmp_path.name}")

    # Use persistent fixture
    repo_path = Path("tests/fixtures/repo_with_docker")

    result = DockerScanner(repo_path).scan()

    logger.info("DockerScanner result: %s", result)

    assert result is not None
    assert result["type"] == "infrastructure"
    assert result["name"] == "docker"

    assert result["dockerfiles"]["detected"] is True
    assert result["dockerfiles"]["count"] == 2
    dockerfiles = [Path(p).name for p in result["dockerfiles"]["files"]]
    assert "Dockerfile" in dockerfiles
    assert "Dockerfile.dev" in dockerfiles

    assert result["compose_files"]["detected"] is True
    assert result["compose_files"]["count"] == 1
    compose_files = [Path(p).name for p in result["compose_files"]["files"]]
    assert "docker-compose.yml" in compose_files

    assert result["ignore_files"]["detected"] is True
    assert result["ignore_files"]["count"] == 1
    ignore_files = [Path(p).name for p in result["ignore_files"]["files"]]
    assert ".dockerignore" in ignore_files


def test_docker_scanner_returns_none_without_docker(tmp_path):
    settings.log_dir = str(tmp_path / "logs")
    logger = get_logger(f"test_docker_scanner_none_{tmp_path.name}")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").touch()

    result = DockerScanner(tmp_path).scan()

    logger.info("DockerScanner result (no docker): %s", result)

    assert result is None
