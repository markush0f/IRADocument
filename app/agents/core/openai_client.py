from typing import List, Dict, Any, Optional, AsyncGenerator
import os
from openai import AsyncOpenAI
from app.agents.core.base import BaseLLMClient
from app.core.logger import get_logger

logger = get_logger(__name__)


class OpenAIClient(BaseLLMClient):
    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None):
        self.model = model
        # If api_key is not provided, AsyncOpenAI will look for 'OPENAI_API_KEY' env var
        self.client = AsyncOpenAI(api_key=api_key, max_retries=5)

    async def generate(self, prompt: str, system: Optional[str] = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=self.model, messages=messages
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise

    async def process_messages(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Send messages + optional tools to OpenAI.
        Returns a dict compatible with our AgentExecutor expectation:
        {
          "role": "assistant",
          "content": "...",
          "tool_calls": [...]
        }
        """
        try:
            # Prepare kwargs
            kwargs: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = await self.client.chat.completions.create(**kwargs)
            message = response.choices[0].message

            # Convert OpenAI format to our internal dict format
            result = {
                "role": "assistant",
                "content": message.content,
            }

            if message.tool_calls:
                # Convert OpenAI tool calls to dicts
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message.tool_calls
                ]

            return result

        except Exception as e:
            logger.error(f"OpenAI chat completion failed: {e}")
            raise

    async def stream_generate(
        self, prompt: str, system: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            stream = await self.client.chat.completions.create(
                model=self.model, messages=messages, stream=True
            )
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
            raise
