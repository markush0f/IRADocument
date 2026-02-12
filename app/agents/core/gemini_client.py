from typing import List, Dict, Any, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from .base import BaseLLMClient
from app.core.logger import get_logger

logger = get_logger(__name__)


class GeminiClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-lite"):
        """
        Initialize Gemini client.
        Default model is 'gemini-2.0-flash-lite' for speed/cost efficiency.
        """
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for GeminiClient")

        genai.configure(api_key=api_key)
        self.model_name = model
        self.client = genai.GenerativeModel(model)

        # Configure safety settings to be less restrictive for code documentation
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        tools: Optional[List[Dict]] = None,
        response_format: Optional[Dict] = None,
    ) -> str:
        """
        Generate a text response from Gemini.
        Adapts OpenAI-style messages to Gemini content format.
        """
        # Convert standard messages to Gemini history format effectively
        # Gemini uses 'user' and 'model' roles.
        # System instructions are set at model init, but we can prepend them here.

        system_instruction = ""
        chat_history = []

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")

            if role == "system":
                system_instruction += f"{content}\n"
            elif role == "user":
                chat_history.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                chat_history.append({"role": "model", "parts": [content]})

        # If we have a system instruction, we should ideally set it on model init
        # But since we reuse the client, let's prepend it to the first user message or use count_tokens trick
        # Simplified approach: Prepend system prompt to first user message if possible
        if system_instruction and chat_history:
            chat_history[0]["parts"][
                0
            ] = f"System Instruction:\n{system_instruction}\n\nUser Request:\n{chat_history[0]['parts'][0]}"
        elif system_instruction and not chat_history:
            chat_history.append({"role": "user", "parts": [system_instruction]})

        try:
            # Generation config
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
                response_mime_type=(
                    "application/json"
                    if response_format and response_format.get("type") == "json_object"
                    else "text/plain"
                ),
            )

            # Retry with exponential backoff for rate limit errors (429)
            import asyncio

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = await self.client.generate_content_async(
                        contents=chat_history,
                        generation_config=generation_config,
                        safety_settings=self.safety_settings,
                    )
                    return response.text
                except Exception as retry_err:
                    if "429" in str(retry_err) and attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5
                        logger.warning(
                            f"Rate limited (429). Retrying in {wait_time}s "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        raise retry_err

        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise e

    async def generate_json(
        self, messages: List[Dict[str, str]], model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates JSON response using Gemini's structured output mode.
        """
        import json

        response_text = await self.generate_response(
            messages, model=model, response_format={"type": "json_object"}
        )

        # Clean up markdown code blocks if present (Gemini sometimes adds ```json ... ```)
        cleaned_text = response_text.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from Gemini: {cleaned_text}")
            return {"error": "Invalid JSON response", "raw": cleaned_text}

    # Implement other abstract methods as pass/basic for now
    async def generate(self, prompt: str, **kwargs) -> str:
        return await self.generate_response(
            [{"role": "user", "content": prompt}], **kwargs
        )

    async def process_messages(self, messages, tools=None):
        """
        Process messages and return OpenAI-compatible response dict.
        """
        # If tools are provided, we need to instruct Gemini to use JSON mode for tool calls
        # because we are using a simplified tool calling mechanism via parsing.
        if tools:
            import copy

            # Create a copy to avoid mutating the original message history
            messages = copy.deepcopy(messages)

            # Inject tool definitions into system prompt or user message
            tools_desc = "\n".join(
                [
                    f"- {t['function']['name']}: {t['function']['description']}"
                    for t in tools
                ]
            )
            tool_instruction = (
                f"\n\nAVAILABLE TOOLS:\n{tools_desc}\n\n"
                "To use a tool, you MUST respond with a valid JSON object in this format:\n"
                '```json\n{"function": "tool_name", "arguments": {"arg": "value"}}\n```\n'
                "Do not add any other text outside the JSON block if you are calling a tool."
            )

            # Find the last user message to append instructions
            for i in range(len(messages) - 1, -1, -1):
                if messages[i]["role"] == "user":
                    messages[i]["content"] += tool_instruction
                    break

        response_text = await self.generate_response(messages)

        # Return dict compatible with AgentExecutor
        return {"role": "assistant", "content": response_text}

    async def stream_generate(self, messages, **kwargs):
        # Streaming not implemented in this basic client yet
        response = await self.generate_response(messages, **kwargs)
        yield response
