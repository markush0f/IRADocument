import asyncio
import os
import sys
import json
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
from app.agents.core.openai_client import OpenAIClient
from app.agents.architect.agent import ArchitectAgent
from app.agents.scribe.agent import ScribeAgent
from app.core.logger import get_logger

load_dotenv()
logger = get_logger("run_pipeline")

MODEL = "gpt-4o-mini"
OUTPUT_DIR = "wiki_docs"


def resolve_target_modules(
    page_id: str, page_title: str, all_modules: list[str]
) -> list[str]:
    """
    Heuristic to matching a page to relevant code modules.
    Logic ported from old ArchitectAgent.
    """
    keywords = page_id.replace("-", " ").lower().split() + page_title.lower().split()
    unique_keywords = set(k for k in keywords if len(k) > 2)

    targets = []

    # Special Mappings
    if "repository" in page_id or "storage" in page_id:
        unique_keywords.add("storage")
        unique_keywords.add("repository")

    for mod in all_modules:
        if any(k in mod.lower() for k in unique_keywords):
            targets.append(mod)

    # Fallback to broad match if "backend" is the only clue
    if not targets and "backend" in unique_keywords:
        return ["app"]  # The whole app

    # Limit context
    return targets[:5]


async def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not found.")
        return

    client = OpenAIClient(model=MODEL, api_key=api_key)
    architect = ArchitectAgent(client)
    scribe = ScribeAgent(client)

    # ==========================================
    # PHASE 1: MINER (Load existing output)
    # ==========================================
    miner_file = "miner_output.json"
    if not os.path.exists(miner_file):
        logger.error(f"{miner_file} not found. Run miner first.")
        return

    logger.info("loading miner output...")
    with open(miner_file, "r") as f:
        miner_data = json.load(f)

    # ==========================================
    # PHASE 2: ARCHITECT (Plan)
    # ==========================================
    logger.info("🧠 Architect is planning navigation...")
    plan_file = "wiki_plan.json"

    # Check if we already have a plan to save time/money
    if os.path.exists(plan_file):
        logger.info(f"Loading existing plan from {plan_file}")
        with open(plan_file, "r") as f:
            plan_data = json.load(f)
            # Re-wrap in object if needed, or just use dict if we're lazy.
            # But the Scribe needs to iterate a tree.
            # Let's verify structure. Scribe uses 'wiki_plan.json' ? No, Scribe takes arguments.
    else:
        # Run Architect
        plan = await architect.plan_navigation(miner_data)
        if not plan:
            logger.error("Architect failed to plan.")
            return

        # Save output
        plan_data = plan.model_dump()
        with open(plan_file, "w") as f:
            json.dump(plan_data, f, indent=2)
        logger.info("Plan saved.")

        # Save Sidebar for Frontend
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(f"{OUTPUT_DIR}/sidebar.json", "w") as f:
            json.dump(plan_data, f, indent=2)

    # ==========================================
    # PHASE 3: SCRIBE (Write)
    # ==========================================
    logger.info("✍️ Scribe is starting to write pages...")

    # Flatten the tree to get a list of tasks
    pages_to_write = []

    def traverse(nodes):
        for node in nodes:
            # Plan data might be a dict (if loaded from json) or object (if fresh)
            # Let's handle dict for simplicity since we might load from file
            if isinstance(node, dict):
                node_type = node.get("type")
                children = node.get("children", [])
            else:
                node_type = node.type
                children = node.children

            if node_type == "page":
                pages_to_write.append(node)

            if children:
                traverse(children)

    if isinstance(plan_data, dict):
        traverse(plan_data.get("tree", []))
    else:
        traverse(plan_data.tree)

    # Pre-calculate module list for resolution
    # (Borrowing logic from Architect/Scribe utils)
    raw_results = miner_data.get("results", [])
    all_modules = set()
    for item in raw_results:
        fpath = item.get("file", "")
        parent = os.path.dirname(fpath)
        if parent:
            all_modules.add(parent)
    all_modules = list(all_modules)

    # Execute Scribe Loop
    total = len(pages_to_write)
    for i, page in enumerate(pages_to_write):
        # Handle dict vs object
        p_id = page.get("id") if isinstance(page, dict) else page.id
        p_label = page.get("label") if isinstance(page, dict) else page.label

        target_modules = resolve_target_modules(p_id, p_label, all_modules)

        logger.info(
            f"[{i+1}/{total}] Writing '{p_label}' (Modules: {target_modules})..."
        )

        # Determine "Page Type" based on keywords
        page_type = "module_reference"
        if "overview" in p_id or "architecture" in p_label.lower():
            page_type = "architecture_overview"

        try:
            wiki_page = await scribe.write_page(
                page_id=p_id,
                page_type=page_type,
                page_title=p_label,
                target_modules=target_modules,
                miner_output=miner_data,
            )

            if wiki_page:
                fname = f"{OUTPUT_DIR}/{p_id}.json"
                with open(fname, "w") as f:
                    f.write(wiki_page.model_dump_json(indent=2))
                logger.info(f"Saved {fname}")

            # Rate limit
            time.sleep(2)

        except Exception as e:
            logger.error(f"Failed to write {p_id}: {e}")

    logger.info("Pipeline Complete! 🚀")


if __name__ == "__main__":
    asyncio.run(main())
