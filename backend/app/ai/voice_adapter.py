"""
Voice layer — provider-agnostic STT/TTS, same pattern as llm_adapter.py. Anthropic doesn't
offer speech endpoints, so this defaults to OpenAI's Whisper (STT) and TTS APIs; swap in a
self-hosted Whisper/Coqui setup by writing a new provider class here without touching the
voice API route.
"""
from abc import ABC, abstractmethod

import httpx

from app.core.config import settings


class SpeechToTextProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, filename: str, content_type: str) -> str:
        raise NotImplementedError


class TextToSpeechProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """Returns raw audio bytes (mp3)."""
        raise NotImplementedError


class OpenAIWhisperProvider(SpeechToTextProvider):
    _ENDPOINT = "https://api.openai.com/v1/audio/transcriptions"

    async def transcribe(self, audio_bytes: bytes, filename: str, content_type: str) -> str:
        headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
        files = {"file": (filename, audio_bytes, content_type)}
        data = {"model": "whisper-1"}
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self._ENDPOINT, headers=headers, files=files, data=data)
            response.raise_for_status()
            return response.json()["text"]


class OpenAITTSProvider(TextToSpeechProvider):
    _ENDPOINT = "https://api.openai.com/v1/audio/speech"

    async def synthesize(self, text: str) -> bytes:
        headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "content-type": "application/json"}
        payload = {"model": "tts-1", "voice": "alloy", "input": text}
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self._ENDPOINT, headers=headers, json=payload)
            response.raise_for_status()
            return response.content


def get_stt_provider() -> SpeechToTextProvider:
    return OpenAIWhisperProvider()


def get_tts_provider() -> TextToSpeechProvider:
    return OpenAITTSProvider()
