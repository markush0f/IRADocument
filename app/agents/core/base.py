from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator


class BaseLLMClient(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """Generate a complete response for a given prompt."""
        pass

    @abstractmethod
    async def process_messages(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Process a conversation history and return the next message."""
        pass

    @abstractmethod
    async def stream_generate(
        self, prompt: str, system: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Stream the generation of a response."""
        pass
