import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.core.ollama_client import OllamaClient
from app.agents.miner.agent import MinerAgent
from app.core.logger import get_logger

logger = get_logger("test_miner")


async def test_miner_batch():
    # 1. Initialize Client and Agent
    # Change model if needed
    client = OllamaClient(model="qwen2.5-coder:latest", host="http://localhost:11434")
    miner = MinerAgent(client=client)

    # 2. Define directories to scan (Models & Agents Core)
    scan_dirs = ["app/models", "app/agents/core"]
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    files_to_analyze = []

    # Collect all python files
    for d in scan_dirs:
        abs_d = os.path.join(root_dir, d)
        if not os.path.exists(abs_d):
            print(f"Warning: Directory {abs_d} not found.")
            continue

        for root, _, files in os.walk(abs_d):
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    files_to_analyze.append(os.path.join(root, file))

    print(f"--- Batch Analyzing {len(files_to_analyze)} files ---")

    for i, abs_path in enumerate(files_to_analyze):
        rel_path = os.path.relpath(abs_path, root_dir)
        print(f"\n[{i+1}/{len(files_to_analyze)}] Analyzing: {rel_path}...")

        try:
            # Note: For production use a robust asynchronous file reader, but for scripts open() is fine
            with open(abs_path, "r") as f:
                content = f.read()

            result = await miner.analyze_file(file_path=rel_path, file_content=content)

            if result:
                for c in result.conclusions:
                    print(f"  -> [{c.impact}] [{c.topic}] {c.statement}")
            else:
                print("  -> [ERROR] No results returned (or Miner failed).")

        except Exception as e:
            print(f"  -> [CRITICAL] Failed to process file: {e}")


if __name__ == "__main__":
    asyncio.run(test_miner_batch())
