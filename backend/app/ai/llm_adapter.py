"""
LLM layer — provider-agnostic adapter so the orchestrator never depends on a specific
vendor's SDK/API shape directly. Swapping providers means writing a new class here and
changing one line of wiring, not touching chat logic or the WebSocket handler.
"""
from abc import ABC, abstractmethod

import httpx

from app.core.config import settings


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, system_prompt: str, messages: list[dict[str, str]]) -> str:
        """messages: list of {"role": "user"|"assistant", "content": str}, oldest first."""
        raise NotImplementedError


class AnthropicProvider(LLMProvider):
    _ENDPOINT = "https://api.anthropic.com/v1/messages"

    async def generate(self, system_prompt: str, messages: list[dict[str, str]]) -> str:
        headers = {
            "x-api-key": settings.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": settings.ANTHROPIC_MODEL,
            "max_tokens": settings.LLM_MAX_TOKENS,
            "system": system_prompt,
            "messages": messages,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self._ENDPOINT, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        # Concatenate any text blocks in the response (tool_use blocks are ignored here —
        # no tools are wired into this call yet).
        text_parts = [block["text"] for block in data.get("content", []) if block.get("type") == "text"]
        return "".join(text_parts).strip()


def get_llm_provider() -> LLMProvider:
    return AnthropicProvider()


def generate_sync(system_prompt: str, messages: list[dict[str, str]], max_tokens: int | None = None) -> str:
    """Synchronous variant for use in Celery workers, which run outside the asyncio event loop."""
    headers = {
        "x-api-key": settings.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": settings.ANTHROPIC_MODEL,
        "max_tokens": max_tokens or settings.LLM_MAX_TOKENS,
        "system": system_prompt,
        "messages": messages,
    }
    with httpx.Client(timeout=30.0) as client:
        response = client.post(AnthropicProvider._ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    text_parts = [block["text"] for block in data.get("content", []) if block.get("type") == "text"]
    return "".join(text_parts).strip()
