import os
from pathlib import Path
from typing import Dict, Any


class PromptLoader:
    """
    Utility class to load prompts from text files.
    """

    PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

    @classmethod
    def load_prompt(cls, name: str, **kwargs) -> str:
        """
        Loads a prompt by name and formats it with provided variables.
        """
        file_path = cls.PROMPTS_DIR / f"{name}.txt"

        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            template = f.read().strip()

        return template.format(**kwargs)
