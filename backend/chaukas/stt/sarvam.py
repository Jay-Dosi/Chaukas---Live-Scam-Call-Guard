"""Sarvam AI STT adapter — PRD §8.5.

Implemented against Sarvam's current official streaming API docs.
Uses WebSocket streaming with appropriate auth and audio format.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
from typing import AsyncIterator

import websockets
from websockets.client import WebSocketClientProtocol

from chaukas.stt.base import SttEvent, SttProvider, SttSession


class SarvamSttSession:
    """Sarvam streaming STT session."""

    def __init__(self, api_key: str, lang: str):
        self.api_key = api_key
        self.lang = self._map_lang(lang)
        self._ws: WebSocketClientProtocol | None = None
        self._queue: asyncio.Queue[SttEvent] = asyncio.Queue()
        self._receive_task: asyncio.Task | None = None
        self._segment_counter = 0

    def _map_lang(self, lang: str) -> str:
        if lang.startswith("hi"):
            return "hi-IN"
        if lang.startswith("en"):
            return "en-IN"
        return "hi-IN"  # default

    async def push(self, pcm16: bytes) -> None:
        if self._ws and not self._ws.closed:
            # Sarvam expects base64-encoded PCM16
            audio_b64 = base64.b64encode(pcm16).decode("ascii")
            await self._ws.send(json.dumps({"audio": audio_b64}))

    async def stop(self) -> None:
        if self._ws and not self._ws.closed:
            await self._ws.send(json.dumps({"type": "end"}))
            await self._ws.close()
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        await self._queue.put(SttEvent(kind="closed"))

    def events(self) -> AsyncIterator[SttEvent]:
        async def _gen():
            while True:
                try:
                    event = await asyncio.wait_for(self._queue.get(), timeout=30.0)
                    yield event
                    if event.kind == "closed":
                        break
                except asyncio.TimeoutError:
                    yield SttEvent(kind="error", message="Sarvam STT timeout")
                    break
                except Exception as e:
                    yield SttEvent(kind="error", message=str(e))
                    break

        return _gen()

    async def _connect(self) -> None:
        """Establish WebSocket connection to Sarvam."""
        # Sarvam STT streaming endpoint (from official docs)
        url = "wss://api.sarvam.ai/speech-to-text-streaming"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        self._ws = await websockets.connect(url, extra_headers=headers)

        # Send config
        config = {
            "type": "config",
            "language_code": self.lang,
            "model": "saarika:v1",  # current Sarvam model
            "sample_rate": 16000,
            "encoding": "PCM16",
            "interim_results": True,
        }
        await self._ws.send(json.dumps(config))

        # Start receive loop
        self._receive_task = asyncio.create_task(self._receive_loop())

    async def _receive_loop(self) -> None:
        """Process incoming WebSocket messages."""
        try:
            async for message in self._ws:
                data = json.loads(message)
                event_type = data.get("type")

                if event_type == "partial":
                    self._segment_counter += 1
                    await self._queue.put(SttEvent(
                        kind="partial",
                        id=f"seg_{self._segment_counter}",
                        text=data.get("text", ""),
                        t_ms=data.get("timestamp", 0),
                        lang=self.lang,
                    ))
                elif event_type == "final":
                    self._segment_counter += 1
                    await self._queue.put(SttEvent(
                        kind="final",
                        id=f"seg_{self._segment_counter}",
                        text=data.get("text", ""),
                        t_start_ms=data.get("start_timestamp", 0),
                        t_end_ms=data.get("end_timestamp", 0),
                        lang=data.get("language", self.lang),
                    ))
                elif event_type == "error":
                    await self._queue.put(SttEvent(
                        kind="error",
                        message=data.get("message", "Sarvam STT error"),
                    ))
        except Exception as e:
            await self._queue.put(SttEvent(kind="error", message=str(e)))
        finally:
            await self._queue.put(SttEvent(kind="closed"))


class SarvamSttProvider:
    """Sarvam STT provider factory."""

    name = "sarvam"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("SARVAM_API_KEY", "")

    def supports(self, lang: str) -> bool:
        return lang in ("hi-IN", "en-IN", "auto")

    async def open(self, lang: str, sample_rate: int = 16000) -> SttSession:
        if not self.api_key:
            raise ValueError("Sarvam API key not configured")
        session = SarvamSttSession(self.api_key, lang)
        await session._connect()
        return session