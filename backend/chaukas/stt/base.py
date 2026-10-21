"""STT Provider interfaces — PRD §8.5.

All vendor adapters implement these protocols.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncIterator, Protocol


@dataclass
class SttEvent:
    kind: Literal["partial", "final", "error", "closed"]
    id: str | None = None
    text: str | None = None
    t_start_ms: int | None = None
    t_end_ms: int | None = None
    lang: str | None = None
    message: str | None = None


class SttSession(Protocol):
    """An active STT streaming session."""

    async def push(self, pcm16: bytes) -> None:
        """Push 16kHz mono PCM16LE audio chunk."""
        ...

    async def stop(self) -> None:
        """Close the session gracefully."""
        ...

    def events(self) -> AsyncIterator[SttEvent]:
        """Async iterator yielding transcript events."""
        ...


class SttProvider(Protocol):
    """STT provider factory."""

    name: str

    def supports(self, lang: str) -> bool:
        """Return True if this provider supports the given language code."""
        ...

    async def open(self, lang: str, sample_rate: int = 16000) -> SttSession:
        """Open a new streaming session."""
        ...