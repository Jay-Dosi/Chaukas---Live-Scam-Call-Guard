"""No-op TTS provider (fallback when TTS disabled)."""

from __future__ import annotations

from chaukas.tts.base import TtsProvider


class NoneTtsProvider:
    """TTS provider that returns None (no audio)."""

    name = "none"
    voices = []

    async def synthesize(self, text: str, lang: str, voice: str | None) -> bytes | None:
        return None