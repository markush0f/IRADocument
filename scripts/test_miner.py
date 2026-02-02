import asyncio
import os
import sys
import json
import time
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.core.openai_client import OpenAIClient
from app.agents.miner.agent import MinerAgent
from app.core.logger import get_logger

logger = get_logger("test_miner")

# CONFIGURATION
MODEL = "gpt-4o-mini"
BATCH_SIZE = 5  # Batch size
DELAY_BETWEEN_BATCHES = 2.0  # Seconds to wait between batches to respect TPM
MAX_RETRIES = 2


async def analyze_single_file_safe(miner, abs_path, root_dir):
    """Fallback: Analyze a single file safely."""
    rel_path = os.path.relpath(abs_path, root_dir)
    try:
        with open(abs_path, "r") as f:
            content = f.read()
        if not content.strip():
            return None

        # Retry logic for single checking
        for attempt in range(MAX_RETRIES):
            try:
                result = await miner.analyze_file(
                    file_path=rel_path, file_content=content
                )
                if result:
                    res_dict = result.model_dump()
                    res_dict["analysis_duration_seconds"] = 0  # Placeholder
                    res_dict["method"] = "single_fallback"
                    print(f"   ✅ Single Recovery: {rel_path}")
                    return res_dict
            except Exception as e:
                print(f"   ⚠️ Single Attempt {attempt+1} failed for {rel_path}: {e}")
                await asyncio.sleep(1)

        print(f"   ❌ Failed to recover {rel_path} after retries.")
        return None

    except Exception as e:
        print(f"   ❌ Error reading/processing {rel_path}: {e}")
        return None


async def process_batch_robust(miner, batch_files, root_dir):
    """Process a batch. If it fails or is incomplete, fallback to single file processing."""

    # Prepare content
    files_data = []
    for abs_path in batch_files:
        try:
            with open(abs_path, "r") as f:
                content = f.read()
            if content.strip():
                rel_path = os.path.relpath(abs_path, root_dir)
                files_data.append((rel_path, content))
        except Exception:
            pass

    if not files_data:
        return []

    files_map = {p: c for p, c in files_data}
    target_files = set(files_map.keys())

    start_t = time.time()

    # 1. Try Batch
    try:
        print(f"📦 Batch of {len(files_data)}...")
        batch_result = await miner.analyze_batch(files=files_data)

        if batch_result and batch_result.results:
            duration = time.time() - start_t

            # Check coverage
            returned_results = []
            returned_filenames = set()

            for r in batch_result.results:
                d = r.model_dump()
                d["analysis_duration_seconds"] = round(
                    duration / len(batch_result.results), 2
                )
                d["method"] = "batch"
                returned_results.append(d)
                returned_filenames.add(r.file)

            missing = target_files - returned_filenames

            if not missing:
                print(f"   ✅ Batch Perfect ({duration:.2f}s)")
                return returned_results
            else:
                print(f"   ⚠️ Batch Partial. Missing: {len(missing)}. Recovering...")
                # Recover missing only
                for missing_file in missing:
                    # Find absolute path
                    abs_p = os.path.join(root_dir, missing_file)
                    single_res = await analyze_single_file_safe(miner, abs_p, root_dir)
                    if single_res:
                        returned_results.append(single_res)
                return returned_results
        else:
            print("   ⚠️ Batch returned empty. Fallback to sequential.")
            # Fallback below

    except Exception as e:
        print(f"   ⚠️ Batch Failed ({e}). Fallback to sequential.")

    # 2. Fallback: Process ALL files in batch individually
    results = []
    for abs_path in batch_files:
        res = await analyze_single_file_safe(miner, abs_path, root_dir)
        if res:
            results.append(res)
    return results


async def test_miner_robust():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not set.")
        return

    client = OpenAIClient(model=MODEL, api_key=api_key)
    miner = MinerAgent(client=client)

    # Collect Files
    scan_dirs = ["app"]  # Full scan
    # For testing, you can limit this list

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
        f"--- 🛡️  Robust Miner: {len(files_to_analyze)} files. Batch: {BATCH_SIZE}. ---"
    )

    total_start = time.time()
    all_results = []

    # Process sequentially (Batch by Batch)
    for i in range(0, len(files_to_analyze), BATCH_SIZE):
        chunk = files_to_analyze[i : i + BATCH_SIZE]

        batch_results = await process_batch_robust(miner, chunk, root_dir)
        all_results.extend(batch_results)

        # Rate Limit Sleep
        await asyncio.sleep(DELAY_BETWEEN_BATCHES)

    total_duration = time.time() - total_start

    # Save
    output_file = "miner_output.json"
    meta = {
        "total_files": len(files_to_analyze),
        "total_duration_seconds": round(total_duration, 2),
        "model": MODEL,
        "mode": "robust_batch",
        "results": all_results,
    }

    with open(output_file, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\n--- Analysis Complete ---")
    print(f"Total Time: {total_duration:.2f}s")
    print(f"Saved {len(all_results)} analyses to {output_file}")


if __name__ == "__main__":
    asyncio.run(test_miner_robust())
