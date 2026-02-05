import pytest
import json
from unittest.mock import MagicMock
from app.agents.core.base import BaseLLMClient
from app.agents.miner.agent import MinerAgent


class MockLLMClient(BaseLLMClient):
    def __init__(self, model: str = "mock", api_key: str = "mock"):
        self.model = model

    async def generate_response(self, *args, **kwargs):
        pass

    async def generate_json(self, *args, **kwargs):
        pass

    async def generate(self, *args, **kwargs):
        pass

    async def process_messages(self, messages, tools=None):
        """Simulate LLM deciding to call a tool."""
        # For simplicity, we always return the same tool call for this test
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_123",
                    "function": {
                        "name": "submit_conclusions",
                        "arguments": json.dumps(
                            {
                                "file": "test_hello.py",
                                "conclusions": [
                                    {
                                        "topic": "test",
                                        "statement": "Found a hello function",
                                        "impact": "HIGH",
                                    }
                                ],
                            }
                        ),
                    },
                    "type": "function",
                }
            ],
        }

    async def stream_generate(self, *args, **kwargs):
        pass

    async def get_tool_call(
        self,
        tools,
        system_prompt,
        user_message=None,
        temperature=0,
        max_tokens=1000,
        model=None,
        tool_choice="auto",
        tool_calls=None,
    ):
        """Simulate tool call/response for miner."""
        # Check system prompt or user message to distinguish extract_facts vs others
        # Return a tool call to 'submit_facts' with dummy data

        return {
            "type": "tool_call",
            "feature": "submit_facts",
            "args": {
                "file": "test_hello.py",
                "conclusions": [
                    {
                        "topic": "test",
                        "statement": "Found a hello function",
                        "impact": "HIGH",
                    }
                ],
            },
        }


@pytest.fixture
def mock_miner_agent():
    client = MockLLMClient(model="mock-gpt")
    return MinerAgent(client=client)


@pytest.mark.asyncio
async def test_miner_single_file_analysis_mock(mock_miner_agent):
    """Test analyzing a single file with mocked LLM."""
    file_content = "def hello():\n    print('Hello World')"
    file_path = "test_hello.py"

    # We mock the executor inside usage or rely on client.get_tool_call returning a tool that AgentExecutor executes.
    # In AgentExecutor logic (if used by Miner):
    # It calls client.get_tool_call -> returns tool_call -> executes tool -> returns result.

    result = await mock_miner_agent.analyze_file(file_path, file_content)

    assert result is not None
    assert result.file == file_path
    assert result.conclusions[0].topic == "test"
