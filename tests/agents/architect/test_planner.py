import pytest
import os
import json
from unittest.mock import MagicMock
from app.agents.core.base import BaseLLMClient
from app.agents.architect.agent import ArchitectAgent
from app.agents.architect.schema import WikiNavigation


class MockArchitectClient(BaseLLMClient):
    def __init__(self, model: str = "mock", api_key: str = "mock"):
        self.model = model
        self.call_count = 0

    async def generate_response(self, *args, **kwargs):
        pass

    async def generate_json(self, *args, **kwargs):
        pass

    async def generate(self, *args, **kwargs):
        pass

    async def stream_generate(self, *args, **kwargs):
        pass

    async def process_messages(self, messages, tools=None):
        """
        Simulate LLM responses.
        Call 1: Subsystem Detection -> Returns list of subsystems.
        Call 2: Navigation Planning -> Returns WikiNavigation tree.
        """
        self.call_count += 1

        # 1. Subsystem Detector
        if "submit_subsystems" in str(tools):
            return {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call_sub",
                        "function": {
                            "name": "submit_subsystems",
                            "arguments": json.dumps(
                                {
                                    "subsystems": [
                                        {
                                            "name": "Backend API",
                                            "role": "backend",
                                            "technologies": ["FastAPI"],
                                            "root_path": "app",
                                        }
                                    ]
                                }
                            ),
                        },
                        "type": "function",
                    }
                ],
            }

        # 2. Architect Navigation Plan
        if "submit_navigation" in str(tools):
            return {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call_nav",
                        "function": {
                            "name": "submit_navigation",
                            "arguments": json.dumps(
                                {
                                    "project_name": "Test Project",
                                    "detected_subsystems": ["backend"],
                                    "tree": [
                                        {
                                            "id": "backend-api",
                                            "label": "Backend API",
                                            "type": "category",
                                            "children": [
                                                {
                                                    "id": "backend-overview",
                                                    "label": "Overview",
                                                    "type": "page",
                                                    "children": [],
                                                }
                                            ],
                                        }
                                    ],
                                }
                            ),
                        },
                        "type": "function",
                    }
                ],
            }

        return {"role": "assistant", "content": "I don't know what to do."}


@pytest.fixture
def mock_architect_agent():
    client = MockArchitectClient()
    return ArchitectAgent(client=client)


@pytest.fixture
def sample_miner_output():
    """Mock miner output for planning."""
    return {
        "results": [
            {
                "file": "app/main.py",
                "conclusions": [{"topic": "framework", "statement": "Uses FastAPI"}],
            }
        ]
    }


@pytest.mark.asyncio
async def test_architect_plan_navigation_mock(
    mock_architect_agent, sample_miner_output
):
    """Test that architect can generate a plan using mocks."""
    nav = await mock_architect_agent.plan_navigation(sample_miner_output)

    assert nav is not None
    assert nav.project_name == "Test Project"
    assert "backend" in nav.detected_subsystems
    assert len(nav.tree) == 1
    assert nav.tree[0].label == "Backend API"
