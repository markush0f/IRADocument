import tiktoken
from app.core.logger import get_logger

logger = get_logger(__name__)


class Tokenizer:
    _encoding = None
    # Use 'cl100k_base' which is standard for gpt-4, gpt-3.5-turbo.
    # 'o200k_base' is for gpt-4o specifically, but cl100k is safe fallback and widely available.
    MODEL_ENCODING = "cl100k_base"

    @classmethod
    def get_encoding(cls):
        if cls._encoding is None:
            try:
                cls._encoding = tiktoken.get_encoding(cls.MODEL_ENCODING)
            except Exception as e:
                logger.warning(
                    f"Failed to load tokenizer {cls.MODEL_ENCODING}, falling back to p50k_base: {e}"
                )
                cls._encoding = tiktoken.get_encoding("p50k_base")
        return cls._encoding

    @classmethod
    def count(cls, text: str) -> int:
        return len(cls.get_encoding().encode(text))

    @classmethod
    def truncate(cls, text: str, max_tokens: int) -> str:
        """Truncates text to ensure it stays within max_tokens."""
        encoding = cls.get_encoding()
        tokens = encoding.encode(text)

        if len(tokens) <= max_tokens:
            return text

        logger.info(f"Truncating text from {len(tokens)} to {max_tokens} tokens.")
        return (
            encoding.decode(tokens[:max_tokens])
            + "\n...(content truncated by Tokenizer)..."
        )
