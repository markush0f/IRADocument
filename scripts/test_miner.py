import asyncio
import os
import sys
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.core.ollama_client import OllamaClient
from app.agents.miner.agent import MinerAgent
from app.core.logger import get_logger

logger = get_logger("test_miner")

BATCH_SIZE = 5


async def test_miner_batch_scan():
    # 1. Initialize Client and Agent
    client = OllamaClient(model="llama3.1:latest", host="http://localhost:11434")
    miner = MinerAgent(client=client)

    # 2. Define directories
    scan_dirs = ["app"]
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    files_to_analyze = []

    # Collect files
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
        f"--- Batch Scan: Found {len(files_to_analyze)} files. Batch Size: {BATCH_SIZE} ---"
    )

    all_results = []

    # 3. Process in batches
    for i in range(0, len(files_to_analyze), BATCH_SIZE):
        chunk_paths = files_to_analyze[i : i + BATCH_SIZE]
        print(f"\nProcessing Batch {i//BATCH_SIZE + 1} ({len(chunk_paths)} files)...")

        # Prepare batch data (path, content)
        batch_data = []
        for abs_path in chunk_paths:
            rel_path = os.path.relpath(abs_path, root_dir)
            try:
                with open(abs_path, "r") as f:
                    content = f.read()
                if content.strip():
                    batch_data.append((rel_path, content))
            except Exception as e:
                print(f"Skipping {rel_path}: {e}")

        if not batch_data:
            continue

        # Call Agent
        result = await miner.analyze_batch(files=batch_data)

        if result and result.results:
            print(f"✅ Batch Success: Got {len(result.results)} analyses.")
            for r in result.results:
                all_results.append(result.model_dump())  # Store raw dict
                # Print sample
                if r.conclusions:
                    print(f"   -> {r.file}: {r.conclusions[0].statement[:50]}...")
        else:
            print("⚠️  Batch returned no results.")

    # 4. Save output
    output_file = "miner_output_batch.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n--- Analysis Complete ---")
    print(f"Saved {len(all_results)} total file analyses to {output_file}")


if __name__ == "__main__":
    asyncio.run(test_miner_batch_scan())
