"""Mock STT provider for testing and offline development.

Replays transcript fixtures with realistic timing.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import AsyncIterator

from chaukas.stt.base import SttEvent, SttProvider, SttSession


class MockSttSession:
    """Mock STT session that replays a fixture."""

    def __init__(self, fixture_id: str, lang: str):
        self.fixture_id = fixture_id
        self.lang = lang
        self._queue: asyncio.Queue[SttEvent] = asyncio.Queue()
        self._task: asyncio.Task | None = None
        self._stopped = False
        self._fixture = self._load_fixture()

    def _load_fixture(self) -> list[dict]:
        """Load transcript fixture from file."""
        fixture_dir = Path(__file__).parent.parent.parent / "fixtures" / "transcripts"
        path = fixture_dir / f"{self.fixture_id}.json"
        if not path.exists():
            # Default fixture
            return [
                {"id": "1", "text": "Hello, this is a test call.", "is_final": True, "t_start_ms": 0, "t_end_ms": 2000},
                {"id": "2", "text": "I am calling from your bank.", "is_final": True, "t_start_ms": 3000, "t_end_ms": 5000},
            ]
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    async def push(self, pcm16: bytes) -> None:
        """Ignored for mock — fixture drives timing."""
        pass

    async def stop(self) -> None:
        self._stopped = True
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._queue.put(SttEvent(kind="closed"))

    def events(self) -> AsyncIterator[SttEvent]:
        async def _gen():
            for i, segment in enumerate(self._fixture):
                if self._stopped:
                    break

                # Yield partial
                yield SttEvent(
                    kind="partial",
                    id=segment["id"],
                    text=segment["text"],
                    t_ms=segment.get("t_start_ms", i * 3000),
                    lang=self.lang,
                )

                # Simulate processing delay
                await asyncio.sleep(0.05)

                # Yield final
                yield SttEvent(
                    kind="final",
                    id=segment["id"],
                    text=segment["text"],
                    t_start_ms=segment.get("t_start_ms", i * 3000),
                    t_end_ms=segment.get("t_end_ms", (i + 1) * 3000),
                    lang=self.lang,
                )

                await asyncio.sleep(0.1)

        return _gen()


class MockSttProvider:
    """Mock STT provider factory."""

    name = "mock"

    def supports(self, lang: str) -> bool:
        return lang in ("hi-IN", "en-IN", "auto")

    async def open(self, lang: str, sample_rate: int = 16000) -> SttSession:
        # For mock, we need a fixture_id — use a default or pass via context
        fixture_id = "default"
        return MockSttSession(fixture_id, lang)