from pathlib import Path

from app.core.config import settings
from app.core.logger import get_logger
from app.scanners.technologies.javascript import JavaScriptScanner


def test_javascript_scanner_detects_js_and_ts(tmp_path):
    settings.log_dir = str(tmp_path / "logs")
    logger = get_logger(f"test_js_scanner_{tmp_path.name}")
    repo_path = Path("tests/fixtures/repo_with_various_technologies")

    result = JavaScriptScanner(repo_path).scan()

    logger.info("JavaScriptScanner result: %s", result)

    assert result is not None
    assert result["type"] == "ecosystem"
    assert result["name"] == "javascript"
    assert result["languages"]["javascript"]["detected"] is True
    assert result["languages"]["typescript"]["detected"] is True
    assert result["languages"]["javascript"]["count"] == 1
    assert result["languages"]["typescript"]["count"] == 1
    assert result["frameworks"]["detected"] is True
    assert result["frameworks"]["count"] == 2
    assert set(result["frameworks"]["items"]) == {"express", "react"}

    js_paths = {
        Path(path).relative_to(repo_path).as_posix()
        for path in result["languages"]["javascript"]["files"]
    }
    ts_paths = {
        Path(path).relative_to(repo_path).as_posix()
        for path in result["languages"]["typescript"]["files"]
    }

    assert "src/index.js" in js_paths
    assert "src/helper.ts" in ts_paths
    assert all(
        not path.endswith(".py") for path in result["languages"]["javascript"]["files"]
    )
    assert all(
        not path.endswith(".py") for path in result["languages"]["typescript"]["files"]
    )


def test_javascript_scanner_returns_none_without_js_ts(tmp_path):
    settings.log_dir = str(tmp_path / "logs")
    logger = get_logger(f"test_js_scanner_none_{tmp_path.name}")
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend" / "main.py").write_text("print('ok')\n", encoding="utf-8")

    result = JavaScriptScanner(tmp_path).scan()

    logger.info("JavaScriptScanner result (no js/ts): %s", result)

    assert result is None


def test_javascript_scanner_detects_frameworks(tmp_path):
    settings.log_dir = str(tmp_path / "logs")
    logger = get_logger(f"test_js_scanner_frameworks_{tmp_path.name}")
    repo_path = Path("tests/fixtures/repo_with_js_frameworks")

    result = JavaScriptScanner(repo_path).scan()

    logger.info("JavaScriptScanner result (frameworks): %s", result)

    assert result is not None
    assert result["frameworks"]["detected"] is True
    assert result["frameworks"]["count"] == 7
    assert set(result["frameworks"]["items"]) == {
        "angular",
        "astro",
        "express",
        "fastify",
        "next",
        "react",
        "vite",
    }


def test_javascript_scanner_detects_package_managers(tmp_path):
    settings.log_dir = str(tmp_path / "logs")
    logger = get_logger(f"test_js_scanner_pm_{tmp_path.name}")

    # Use persistent fixture that now includes bun.lockb
    repo_path = Path("tests/fixtures/repo_with_js_frameworks")

    result = JavaScriptScanner(repo_path).scan()

    logger.info("JavaScriptScanner result (pm): %s", result)

    assert result is not None
    assert result["package_managers"]["detected"] is True
    # 'npm' might be detected if package-lock.json exists, 'bun' if bun.lockb
    # Checking if 'bun' is in the set of detected package managers
    assert "bun" in result["package_managers"]["items"]
