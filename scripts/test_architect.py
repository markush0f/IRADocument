import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.core.openai_client import OpenAIClient
from app.agents.architect.agent import ArchitectAgent
from app.core.logger import get_logger

logger = get_logger("test_architect")

MODEL = "gpt-4o-mini"


async def test_architect_wiki():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found.")
        return

    # 1. Load Miner Output
    miner_file = "miner_output.json"
    if not os.path.exists(miner_file):
        print(f"❌ {miner_file} not found.")
        return

    print(f"--- Loading {miner_file} ---")
    with open(miner_file, "r") as f:
        miner_data = json.load(f)

    # 2. Initialize Architect
    client = OpenAIClient(model=MODEL, api_key=api_key)
    architect = ArchitectAgent(client=client)

    print(f"--- 🧠 Architect Building DeepWiki... ---")

    # 3. Generate Wiki
    wiki = await architect.generate_wiki(miner_data)

    if wiki:
        print("\n✅ Wiki Structure Generated!")
        print(f"Project: {wiki.project_name}")
        print(f"Total Pages: {len(wiki.pages)}")
        print("Navigation Tree:")
        for nav in wiki.navigation:
            print(f" - {nav.label}")
            for child in nav.children:
                print(f"   - {child.label}")

        # Save JSON
        output_file = "wiki_structure.json"
        with open(output_file, "w") as f:
            f.write(wiki.model_dump_json(indent=2))

        print(f"\n📂 Saved DeepWiki data to {output_file}")
    else:
        print("\n❌ Architect failed.")


if __name__ == "__main__":
    asyncio.run(test_architect_wiki())
