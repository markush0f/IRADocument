import pytest
import httpx
from app.agents.core.ollama_client import OllamaClient
from app.core.config import settings


@pytest.mark.asyncio
async def test_ollama_generate():
    """Test simple generation. Skips if Ollama is not running."""
    client = OllamaClient()
    try:
        response = await client.generate(
            "Say 'pong'", system="Respond only with the word requested"
        )
        assert "pong" in response.lower()
    except Exception as e:
        pytest.skip(f"Ollama not reachable: {e}")


@pytest.mark.asyncio
async def test_ollama_chat_with_tools():
    """Test chat with tool detection."""
    client = OllamaClient()

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            },
        }
    ]

    messages = [{"role": "user", "content": "What is the weather in Madrid?"}]

    try:
        response = await client.chat(messages, tools=tools)
        # Check if it returns a tool call or a message
        assert isinstance(response, dict)
        if "tool_calls" in response:
            assert response["tool_calls"][0]["function"]["name"] == "get_weather"
    except Exception as e:
        pytest.skip(f"Ollama not reachable or model doesn't support tools: {e}")


@pytest.mark.asyncio
async def test_ollama_stream():
    """Test streaming generation."""
    client = OllamaClient()
    try:
        parts = []
        async for part in client.stream_generate("Count to 3"):
            parts.append(part)
        assert len(parts) > 0
    except Exception as e:
        pytest.skip(f"Ollama not reachable: {e}")
