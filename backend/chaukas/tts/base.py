"""TTS Provider interfaces — PRD §8.5."""

from __future__ import annotations

from typing import Protocol


class TtsProvider(Protocol):
    """TTS provider interface."""

    name: str
    voices: list[str]

    async def synthesize(self, text: str, lang: str, voice: str | None) -> bytes | None:
        """Synthesize text to WAV bytes.

        Returns None if TTS is disabled/unavailable.
        """
        ...