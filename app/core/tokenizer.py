import tiktoken
from typing import Dict, Any, Optional, Tuple
from app.core.logger import get_logger

logger = get_logger(__name__)


class Tokenizer:
    """
    Multi-provider token counting and truncation utility.

    Supports accurate counting for:
    - OpenAI models: Uses tiktoken with the correct encoding per model.
    - Gemini models: Character-based approximation calibrated for SentencePiece.
    - Ollama models: Character-based approximation for Llama/Mistral tokenizers.

    """

    _encodings: Dict[str, Any] = {}
    _current_provider: str = "openai"
    _current_model: str = "gpt-4o-mini"

    # Map OpenAI models to their tiktoken encoding
    OPENAI_MODEL_ENCODINGS = {
        "gpt-4o": "o200k_base",
        "gpt-4o-mini": "o200k_base",
        "gpt-4-turbo": "cl100k_base",
        "gpt-4": "cl100k_base",
        "gpt-3.5-turbo": "cl100k_base",
    }

    # Average characters per token for non-OpenAI providers.
    # These values are calibrated approximations:
    # - Gemini uses SentencePiece (Unigram), ~4 chars/token for English code
    # - Ollama models (Llama, Mistral) use SentencePiece (BPE), ~3.8 chars/token
    CHARS_PER_TOKEN_BY_PROVIDER = {
        "gemini": 4.0,
        "ollama": 3.8,
    }

    DEFAULT_ENCODING = "cl100k_base"

    @classmethod
    def configure(cls, provider: str, model: str) -> None:
        """
        Configure the tokenizer for a specific provider and model.
        Call this once before using count/truncate methods.

        Args:
            provider: LLM provider (openai, gemini, ollama).
            model: Model name (e.g., gpt-4o-mini, gemini-1.5-flash).
        """
        cls._current_provider = provider.lower()
        cls._current_model = model
        logger.info(f"Tokenizer configured for provider={provider}, model={model}")

    @classmethod
    def _get_tiktoken_encoding(cls, encoding_name: str):
        """Returns a cached tiktoken encoding instance."""
        if encoding_name not in cls._encodings:
            try:
                cls._encodings[encoding_name] = tiktoken.get_encoding(encoding_name)
                logger.info(f"Loaded tiktoken encoding: {encoding_name}")
            except Exception as e:
                logger.warning(
                    f"Failed to load encoding {encoding_name}, "
                    f"falling back to {cls.DEFAULT_ENCODING}: {e}"
                )
                if cls.DEFAULT_ENCODING not in cls._encodings:
                    cls._encodings[cls.DEFAULT_ENCODING] = tiktoken.get_encoding(
                        cls.DEFAULT_ENCODING
                    )
                cls._encodings[encoding_name] = cls._encodings[cls.DEFAULT_ENCODING]
        return cls._encodings[encoding_name]

    @classmethod
    def _resolve_encoding_name(cls, model: Optional[str] = None) -> str:
        """Resolves the tiktoken encoding name for an OpenAI model."""
        model = model or cls._current_model
        return cls.OPENAI_MODEL_ENCODINGS.get(model, cls.DEFAULT_ENCODING)

    @classmethod
    def _get_chars_per_token(cls, provider: Optional[str] = None) -> float:
        """Returns the estimated chars-per-token ratio for a provider."""
        provider = provider or cls._current_provider
        return cls.CHARS_PER_TOKEN_BY_PROVIDER.get(provider, 4.0)

    @classmethod
    def _is_tiktoken_provider(cls, provider: Optional[str] = None) -> bool:
        """Returns True if the provider supports tiktoken-based counting."""
        provider = provider or cls._current_provider
        return provider == "openai"

    # ==================== PUBLIC API ====================

    @classmethod
    def count(
        cls,
        text: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> int:
        """
        Count the number of tokens in a text string.

        Args:
            text: The text to count tokens for.
            provider: Override the configured provider.
            model: Override the configured model.

        Returns:
            Estimated token count.
        """
        if not text:
            return 0

        provider = provider or cls._current_provider
        model = model or cls._current_model

        if cls._is_tiktoken_provider(provider):
            encoding_name = cls._resolve_encoding_name(model)
            encoding = cls._get_tiktoken_encoding(encoding_name)
            return len(encoding.encode(text))

        # Character-based approximation for Gemini / Ollama
        chars_per_token = cls._get_chars_per_token(provider)
        return max(1, int(len(text) / chars_per_token))

    @classmethod
    def count_batch(
        cls,
        texts: list,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> int:
        """Count total tokens across multiple text strings."""
        return sum(cls.count(t, provider, model) for t in texts if t)

    @classmethod
    def truncate(
        cls,
        text: str,
        max_tokens: int,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> str:
        """
        Truncates text to stay within max_tokens.

        For OpenAI: uses exact tiktoken-based truncation.
        For others: converts token limit to character limit and truncates.
        """
        if not text:
            return text

        provider = provider or cls._current_provider

        if cls._is_tiktoken_provider(provider):
            model = model or cls._current_model
            encoding_name = cls._resolve_encoding_name(model)
            encoding = cls._get_tiktoken_encoding(encoding_name)
            tokens = encoding.encode(text)

            if len(tokens) <= max_tokens:
                return text

            logger.info(
                f"Truncating text from {len(tokens)} to {max_tokens} tokens "
                f"(encoding={encoding_name})"
            )
            return encoding.decode(tokens[:max_tokens]) + "\n...(content truncated)..."

        # Character-based truncation for non-tiktoken providers
        chars_per_token = cls._get_chars_per_token(provider)
        max_chars = int(max_tokens * chars_per_token)
        estimated_tokens = max(1, int(len(text) / chars_per_token))

        if estimated_tokens <= max_tokens:
            return text

        logger.info(
            f"Truncating text from ~{estimated_tokens} to ~{max_tokens} tokens "
            f"(~{max_chars} chars, provider={provider})"
        )
        return text[:max_chars] + "\n...(content truncated)..."

    @classmethod
    def estimate_cost(
        cls,
        text: str,
        cost_per_million: float,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Tuple[int, float]:
        """
        Estimates the cost for processing a text.

        Args:
            text: The text to estimate cost for.
            cost_per_million: Cost per million tokens (USD).
            provider: Override the configured provider.
            model: Override the configured model.

        Returns:
            Tuple of (token_count, estimated_cost_usd).
        """
        token_count = cls.count(text, provider, model)
        cost = (token_count / 1_000_000) * cost_per_million
        return token_count, round(cost, 6)

    @classmethod
    def get_info(cls) -> Dict[str, Any]:
        """Returns current tokenizer configuration for debugging."""
        provider = cls._current_provider
        model = cls._current_model

        info = {
            "provider": provider,
            "model": model,
            "method": "tiktoken" if cls._is_tiktoken_provider() else "char_estimate",
        }

        if cls._is_tiktoken_provider():
            info["encoding"] = cls._resolve_encoding_name()
        else:
            info["chars_per_token"] = cls._get_chars_per_token()

        return info
