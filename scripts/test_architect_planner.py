import asyncio
import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.core.openai_client import OpenAIClient
from app.agents.architect.agent import ArchitectAgent
from app.core.logger import get_logger

logger = get_logger("test_architect_planner")
MODEL = "gpt-4o-mini"


async def test_planner():
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAIClient(model=MODEL, api_key=api_key)
    architect = ArchitectAgent(client=client)

    # 1. Load Data
    if not os.path.exists("miner_output.json"):
        print("❌ miner_output.json missing")
        return

    with open("miner_output.json", "r") as f:
        miner_data = json.load(f)

    # 2. Run Planner
    print("\n🧠 Architect is analyzing project structure...")
    nav = await architect.plan_navigation(miner_data)

    if not nav:
        print("❌ Plan failed.")
        return

    # 3. Output Result
    print("\n✅ Navigation Plan Generated:")
    print(f"Project: {nav.project_name}")
    print(f"Detected Subsystems: {nav.detected_subsystems}")

    print("\n--- Tree Structure ---")
    print(json.dumps(nav.model_dump()["tree"], indent=2))

    # Save for Scribe later
    with open("wiki_plan.json", "w") as f:
        f.write(nav.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(test_planner())
