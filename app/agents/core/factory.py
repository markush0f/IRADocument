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
        elif provider == "openai":
            from .openai_client import OpenAIClient

            return OpenAIClient(
                model=kwargs.get("model", "gpt-4o-mini"),
                api_key=kwargs.get("api_key") or settings.openai_api_key,
            )
        elif provider == "gemini":
            from .gemini_client import GeminiClient

            return GeminiClient(
                api_key=kwargs.get("api_key") or settings.gemini_api_key,
                model=kwargs.get("model", "gemini-pro-latest"),
            )
        # More models can be added here
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
