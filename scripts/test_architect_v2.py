import asyncio
import os
import sys
import json
import time
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.core.openai_client import OpenAIClient
from app.agents.architect.agent import ArchitectAgent
from app.core.logger import get_logger

logger = get_logger("test_architect_v2")
MODEL = "gpt-4o-mini"


async def test_lazy_wiki():
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAIClient(model=MODEL, api_key=api_key)
    architect = ArchitectAgent(client=client)

    # 1. Load Data
    with open("miner_output.json", "r") as f:
        miner_data = json.load(f)

    # 2. Plan Navigation
    print("\n🗺️  Planning Navigation Tree...")
    nav = await architect.plan_navigation(miner_data)

    if not nav:
        print("❌ Navigation failed.")
        return

    # Save Sidebar
    with open("wiki_sidebar.json", "w") as f:
        f.write(nav.model_dump_json(indent=2))
    print("✅ START: Saved wiki_sidebar.json")

    # 3. Generate Pages
    pages_to_generate = []

    def collect_pages(nodes):
        for node in nodes:
            if node.type == "page":
                pages_to_generate.append(node)
            if node.children:
                collect_pages(node.children)

    collect_pages(nav.tree)

    print(
        f"\n📚 Found {len(pages_to_generate)} pages in plan. Generating detailed content for ALL pages..."
    )

    for i, node in enumerate(pages_to_generate):
        print(
            f"   [{i+1}/{len(pages_to_generate)}] Writing content for: {node.label} ({node.id})..."
        )
        try:
            page_detail = await architect.write_page(
                page_id=node.id,
                page_title=node.label,
                related_modules=[],
                miner_output=miner_data,
            )

            if page_detail:
                fname = f"wiki_page_{node.id}.json"
                with open(fname, "w") as f:
                    f.write(page_detail.model_dump_json(indent=2))
                print(
                    f"     ✅ Saved {fname} ({len(page_detail.content_markdown)} chars)"
                )
            else:
                print(f"     ❌ Failed to generate {node.id}")

            # Rate Limit Protection (5 seconds sleep between heavy generations)
            await asyncio.sleep(5.0)

        except Exception as e:
            print(f"     ❌ Critical error on {node.id}: {e}")


if __name__ == "__main__":
    asyncio.run(test_lazy_wiki())
