import asyncio
import os
import sys
import json
import time
from dotenv import load_dotenv

# Load env vars from .env file
load_dotenv()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.core.openai_client import OpenAIClient
from app.agents.miner.agent import MinerAgent
from app.core.logger import get_logger

logger = get_logger("test_miner")

# CONFIGURATION
MODEL = "gpt-4o-mini"
CONCURRENCY_LIMIT = 20  # Process 20 files in parallel (OpenAI handles this easily)


async def scan_file(miner, semaphore, abs_path, rel_path):
    """Analyze a single file with concurrency control."""
    async with semaphore:
        start_t = time.time()
        try:
            with open(abs_path, "r") as f:
                content = f.read()

            if not content.strip():
                return None

            result = await miner.analyze_file(file_path=rel_path, file_content=content)
            duration = time.time() - start_t

            if result:
                res_dict = result.model_dump()
                res_dict["analysis_duration_seconds"] = round(duration, 2)
                # print(f"✅ {rel_path} ({duration:.2f}s)")
                return res_dict
            else:
                print(f"⚠️ {rel_path} - No results")
                return None

        except Exception as e:
            print(f"❌ {rel_path} - Failed: {e}")
            return None


async def test_miner_openai_concurrent():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY environment variable is not set.")
        return

    # 1. Initialize Client
    client = OpenAIClient(model=MODEL, api_key=api_key)
    miner = MinerAgent(client=client)

    # 2. Collect Files
    scan_dirs = ["app"]
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    files_to_analyze = []

    print("--- Collecting files... ---")
    for d in scan_dirs:
        abs_d = os.path.join(root_dir, d)
        for root, _, files in os.walk(abs_d):
            if "__pycache__" in root:
                continue
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    files_to_analyze.append(os.path.join(root, file))

    print(
        f"--- 🚀 OpenAI Scan: {len(files_to_analyze)} files. Concurrency: {CONCURRENCY_LIMIT} ---"
    )

    total_start = time.time()
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    tasks = []

    # 3. Launch Tasks
    for abs_path in files_to_analyze:
        rel_path = os.path.relpath(abs_path, root_dir)
        tasks.append(scan_file(miner, semaphore, abs_path, rel_path))

    # 4. Wait for all
    print("Processing...")
    results = await asyncio.gather(*tasks)

    # Filter Nones
    valid_results = [r for r in results if r is not None]

    total_duration = time.time() - total_start

    # 5. Save Output
    output_file = "miner_output.json"
    meta = {
        "total_files": len(files_to_analyze),
        "total_duration_seconds": round(total_duration, 2),
        "concurrency": CONCURRENCY_LIMIT,
        "results": valid_results,
    }

    with open(output_file, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\n--- Analysis Complete ---")
    print(
        f"Total Time: {total_duration:.2f}s (Avg: {total_duration/len(files_to_analyze):.2f}s/file)"
    )
    print(f"Saved {len(valid_results)} analyses to {output_file}")


if __name__ == "__main__":
    asyncio.run(test_miner_openai_concurrent())
