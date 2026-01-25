from typing import AsyncGenerator, Optional, List, Dict
import ollama
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class OllamaClient:
    def __init__(self, host: Optional[str] = None, model: Optional[str] = None):
        self.host = host or settings.ollama_base_url
        self.model = model or settings.ollama_model
        self.client = ollama.AsyncClient(host=self.host)

    async def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """Generate a complete response for a given prompt."""
        try:
            response = await self.client.generate(
                model=self.model, prompt=prompt, system=system or ""
            )
            return response.get("response", "")
        except Exception as e:
            logger.error(f"Error generating response from Ollama library: {e}")
            raise

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """Send a chat-like conversation to Ollama."""
        try:
            response = await self.client.chat(model=self.model, messages=messages)
            return response.get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Error in chat with Ollama library: {e}")
            raise

    async def stream_generate(
        self, prompt: str, system: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Stream the generation of a response."""
        try:
            async for part in await self.client.generate(
                model=self.model, prompt=prompt, system=system or "", stream=True
            ):
                yield part.get("response", "")
        except Exception as e:
            logger.error(f"Error streaming response from Ollama library: {e}")
            raise
