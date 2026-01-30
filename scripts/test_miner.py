import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.core.ollama_client import OllamaClient
from app.agents.miner.agent import MinerAgent
from app.core.logger import get_logger

logger = get_logger("test_miner")


async def test_miner_full_scan():
    # 1. Initialize Client and Agent
    client = OllamaClient(model="llama3.1:latest", host="http://localhost:11434")
    miner = MinerAgent(client=client)

    # 2. Define root to scan (Everything in app/)
    scan_dirs = ["app"]
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    files_to_analyze = []

    # Collect all python files
    print("--- Collecting files... ---")
    for d in scan_dirs:
        abs_d = os.path.join(root_dir, d)
        for root, _, files in os.walk(abs_d):
            # Ignore __pycache__ and generated files
            if "__pycache__" in root:
                continue

            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    files_to_analyze.append(os.path.join(root, file))

    print(f"--- Full Scan: Found {len(files_to_analyze)} files to analyze ---")

    all_results = []

    for i, abs_path in enumerate(files_to_analyze):
        rel_path = os.path.relpath(abs_path, root_dir)
        print(f"\n[{i+1}/{len(files_to_analyze)}] Analyzing: {rel_path}...")

        try:
            with open(abs_path, "r") as f:
                content = f.read()

            # Skip empty files
            if not content.strip():
                continue

            result = await miner.analyze_file(file_path=rel_path, file_content=content)

            if result:
                # Convert to dict for JSON serialization
                result_dict = result.model_dump()
                all_results.append(result_dict)

                # Live print brief summary
                for c in result.conclusions[:2]:  # Show first 2 only to avoid spam
                    print(f"  -> [{c.impact}] {c.statement[:60]}...")
            else:
                print("  -> [WARN] No results returned.")

        except Exception as e:
            print(f"  -> [CRITICAL] Failed to process file: {e}")

    # 3. Save to JSON
    output_file = "miner_output.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n--- Analysis Complete ---")
    print(f"Saved {len(all_results)} file analyses to {output_file}")


if __name__ == "__main__":
    import json

    asyncio.run(test_miner_full_scan())
