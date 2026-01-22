from pathlib import Path
from app.scanners.technologies.javascript import JavaScriptScanner


scanner = JavaScriptScanner(Path("."))