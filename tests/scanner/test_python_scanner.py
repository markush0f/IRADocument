from pathlib import Path

from app.core.config import settings
from app.core.logger import get_logger
from app.scanners.technologies.python import PythonScanner


def test_python_scanner_detects_frameworks(tmp_path):
    settings.log_dir = str(tmp_path / "logs")
    logger = get_logger(f"test_py_scanner_frameworks_{tmp_path.name}")
    repo_path = Path("tests/fixtures/repo_with_python_technologies")

    result = PythonScanner(repo_path).scan()

    logger.info("PythonScanner result: %s", result)

    assert result is not None
    assert result["type"] == "ecosystem"
    assert result["name"] == "python"
    assert result["languages"]["python"]["detected"] is True
    assert result["languages"]["python"]["count"] >= 1  # main.py and manage.py

    # Check specific frameworks
    frameworks = set(result["frameworks"]["items"])
    expected_frameworks = {
        "django",
        "fastapi",
        "flask",
        "numpy",
        "pandas",
        "pytest",
    }

    assert expected_frameworks.issubset(frameworks)
    assert result["frameworks"]["detected"] is True
    assert result["frameworks"]["count"] >= len(expected_frameworks)

    # Check package managers
    package_managers = set(result["package_managers"]["items"])
    assert "pip" in package_managers
    # We also added uv.lock and environment.yml to this fixture
    assert "uv" in package_managers
    assert "conda" in package_managers
    assert result["package_managers"]["detected"] is True


def test_python_scanner_returns_none_without_python(tmp_path):
    settings.log_dir = str(tmp_path / "logs")
    logger = get_logger(f"test_py_scanner_none_{tmp_path.name}")
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend" / "index.js").write_text(
        "console.log('ok')\n", encoding="utf-8"
    )

    result = PythonScanner(tmp_path).scan()

    logger.info("PythonScanner result (no python): %s", result)

    assert result is None
