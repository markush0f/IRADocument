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
    assert result["language"] == "javascript/typescript"
    assert result["javascript"]["detected"] is True
    assert result["typescript"]["detected"] is True
    assert result["javascript"]["count"] == 1
    assert result["typescript"]["count"] == 1
    assert result["frameworks"]["detected"] is True
    assert result["frameworks"]["count"] == 2
    assert set(result["frameworks"]["items"]) == {"express", "react"}

    js_paths = {Path(path).relative_to(repo_path).as_posix() for path in result["javascript"]["files"]}
    ts_paths = {Path(path).relative_to(repo_path).as_posix() for path in result["typescript"]["files"]}

    assert "src/index.js" in js_paths
    assert "src/helper.ts" in ts_paths
    assert all(not path.endswith(".py") for path in result["javascript"]["files"])
    assert all(not path.endswith(".py") for path in result["typescript"]["files"])


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
