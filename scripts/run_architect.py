import asyncio
import os
import sys
import json
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.core.openai_client import OpenAIClient
from app.agents.architect.agent import ArchitectAgent
from app.core.logger import get_logger

logger = get_logger("run_architect")
MODEL = "gpt-4o-mini"
OUTPUT_DIR = "wiki_docs"


async def test_lazy_wiki_metrics():
    # Setup
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAIClient(model=MODEL, api_key=api_key)
    architect = ArchitectAgent(client=client)

    start_time_all = time.time()
    metadata = {
        "project": "IRADocument",
        "generated_at": datetime.utcnow().isoformat(),
        "total_duration": 0,
        "pages": [],
    }

    # 1. Load Data
    if not os.path.exists("miner_output.json"):
        print("❌ miner_output.json not found")
        return

    with open("miner_output.json", "r") as f:
        miner_data = json.load(f)

    # 2. Plan Navigation
    print("\n🗺️  Planning Navigation Tree...")
    start_time_nav = time.time()
    nav = await architect.plan_navigation(miner_data)
    nav_duration = time.time() - start_time_nav

    if not nav:
        print("❌ Navigation failed.")
        return

    # Save Sidebar
    sidebar_path = os.path.join(OUTPUT_DIR, "sidebar.json")
    with open(sidebar_path, "w") as f:
        f.write(nav.model_dump_json(indent=2))
    print(f"✅ Saved sidebar ({nav_duration:.2f}s)")

    metadata["navigation_duration"] = nav_duration

    # 3. Generate Pages
    pages_to_generate = []

    def collect_pages(nodes):
        for node in nodes:
            if node.type == "page":
                pages_to_generate.append(node)
            if node.children:
                collect_pages(node.children)

    collect_pages(nav.tree)

    print(f"\n📚 Generating {len(pages_to_generate)} detailed pages...")

    for i, node in enumerate(pages_to_generate):
        print(
            f"   [{i+1}/{len(pages_to_generate)}] Writing: {node.label} ({node.id})..."
        )

        page_start = time.time()
        status = "failed"
        exception_msg = None
        chars = 0

        try:
            page_detail = await architect.write_page(
                page_id=node.id,
                page_title=node.label,
                related_modules=[],
                miner_output=miner_data,
            )

            if page_detail:
                fname = os.path.join(OUTPUT_DIR, f"{node.id}.json")
                with open(fname, "w") as f:
                    f.write(page_detail.model_dump_json(indent=2))
                status = "success"
                chars = len(page_detail.content_markdown)
                print(
                    f"     ✅ Saved (len: {chars} chars, time: {time.time()-page_start:.2f}s)"
                )
            else:
                print(f"     ❌ Failed (None result)")

        except Exception as e:
            exception_msg = str(e)
            print(f"     ❌ Error: {e}")

        # Record Metric
        duration = time.time() - page_start
        metadata["pages"].append(
            {
                "id": node.id,
                "label": node.label,
                "status": status,
                "duration": duration,
                "chars": chars,
                "error": exception_msg,
            }
        )

        # Save partial metadata (in case of crash)
        metadata["total_duration"] = time.time() - start_time_all
        with open(os.path.join(OUTPUT_DIR, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)

        # Rate Limit Protection
        await asyncio.sleep(5.0)

    print("\n🏁 Generation Complete.")


if __name__ == "__main__":
    asyncio.run(test_lazy_wiki_metrics())
