from typing import Optional
from .base import BaseLLMClient
from .ollama_client import OllamaClient
from app.core.config import settings


class LLMFactory:
    @staticmethod
    def get_client(provider: str = "ollama", **kwargs) -> BaseLLMClient:
        """Factory to get the appropriate LLM client."""
        provider = provider.lower()

        if provider == "ollama":
            return OllamaClient(host=kwargs.get("host"), model=kwargs.get("model"))
        # More models can be added here
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
