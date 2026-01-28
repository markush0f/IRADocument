from pathlib import Path
from typing import List, Dict, Any
from app.scanners.technologies.python import PythonScanner
from app.scanners.technologies.javascript import JavaScriptScanner
from app.scanners.technologies.docker import DockerScanner
from app.scanners.technologies.database import DatabaseScanner
from app.core.logger import get_logger

logger = get_logger(__name__)


class TechnologyScanner:
    """
    Dedicated scanner for identifying technical stacks across a repository.
    Coordinates specialized scanners for different ecosystems.
    """

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        if not self.repo_path.exists():
            raise FileNotFoundError(f"Repository path not found: {repo_path}")

    def scan(self) -> List[Dict[str, Any]]:
        """
        Executes all registered technology scanners and returns their combined results.
        """
        logger.info(f"Starting whole repository technology scan at: {self.repo_path}")
        scanners = [
            PythonScanner(self.repo_path),
            JavaScriptScanner(self.repo_path),
            DockerScanner(self.repo_path),
            DatabaseScanner(self.repo_path),
        ]

        results = []
        for scanner in scanners:
            scanner_name = scanner.__class__.__name__
            logger.debug(f"Running scanner: {scanner_name}")
            try:
                scanner_result = scanner.scan()
                if scanner_result:
                    ecosystem = scanner_result.get("name", "unknown")
                    logger.info(
                        f"Scanner {scanner_name} detected ecosystem: {ecosystem}"
                    )
                    results.append(scanner_result)
                else:
                    logger.debug(f"Scanner {scanner_name} found no results.")
            except Exception as e:
                logger.error(f"Error in {scanner_name}: {e}")

        logger.info(
            f"Technology scan completed. Total ecosystems detected: {len(results)}"
        )
        return results

    def format_for_llm(self, results: List[Dict[str, Any]]) -> str:
        """
        Transforms raw scanner results into a structured string for AI reasoning.
        Removes file paths and focuses on technology names.
        """
        logger.debug(f"Formatting {len(results)} scanner results for LLM context.")
        if not results:
            logger.warning("No results to format for LLM.")
            return "No specific technologies detected by automated scanners."

        formatted_output = ["### Detected Technology Stack ###"]
        for entry in results:
            ecosystem = entry.get("name", "unknown").upper()
            formatted_output.append(f"\nEcosystem: {ecosystem}")

            for key, val in entry.items():
                if key in ["type", "name"]:
                    continue
                if isinstance(val, dict) and val.get("detected"):
                    # 1. Get raw items/files
                    raw_items = val.get("items") or val.get("files") or val.get("paths")
                    if not raw_items:
                        continue

                    # 2. Cleanup: If they are paths, take only the name/concept
                    clean_items = []
                    for item in raw_items:
                        # If it's a path (contains /), we take the filename or the category
                        if "/" in str(item) or "\\" in str(item):
                            # For Docker and DB, we prefer the category name if it's a path
                            path_obj = Path(item)
                            clean_items.append(path_obj.name)
                        else:
                            clean_items.append(str(item))

                    # 3. Handle duplicates and format
                    unique_items = sorted(list(set(clean_items)))
                    formatted_output.append(
                        f"  - {key.replace('_', ' ').capitalize()}: {', '.join(unique_items[:15])}"
                    )

        logger.debug("LLM tech data formatting completed.")
        return "\n".join(formatted_output)
