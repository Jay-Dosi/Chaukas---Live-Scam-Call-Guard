"""Deepgram STT adapter — PRD §8.5.

Implemented against Deepgram's current official streaming API docs.
Uses WebSocket streaming with appropriate auth and audio format.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import AsyncIterator

import websockets
from websockets.client import WebSocketClientProtocol

from chaukas.stt.base import SttEvent, SttProvider, SttSession


class DeepgramSttSession:
    """Deepgram streaming STT session."""

    def __init__(self, api_key: str, lang: str):
        self.api_key = api_key
        self.lang = self._map_lang(lang)
        self._ws: WebSocketClientProtocol | None = None
        self._queue: asyncio.Queue[SttEvent] = asyncio.Queue()
        self._receive_task: asyncio.Task | None = None
        self._segment_counter = 0

    def _map_lang(self, lang: str) -> str:
        if lang.startswith("hi"):
            return "hi"
        if lang.startswith("en"):
            return "en"
        return "en"

    async def push(self, pcm16: bytes) -> None:
        if self._ws and not self._ws.closed:
            await self._ws.send(pcm16)

    async def stop(self) -> None:
        if self._ws and not self._ws.closed:
            await self._ws.send(json.dumps({"type": "CloseStream"}))
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
                    yield SttEvent(kind="error", message="Deepgram STT timeout")
                    break
                except Exception as e:
                    yield SttEvent(kind="error", message=str(e))
                    break

        return _gen()

    async def _connect(self) -> None:
        """Establish WebSocket connection to Deepgram."""
        # Deepgram streaming endpoint
        url = f"wss://api.deepgram.com/v1/listen?language={self.lang}&model=nova-2&encoding=linear16&sample_rate=16000&interim_results=true&punctuate=true"
        headers = {
            "Authorization": f"Token {self.api_key}",
        }

        self._ws = await websockets.connect(url, extra_headers=headers)

        # Start receive loop
        self._receive_task = asyncio.create_task(self._receive_loop())

    async def _receive_loop(self) -> None:
        """Process incoming WebSocket messages."""
        try:
            async for message in self._ws:
                data = json.loads(message)

                if data.get("type") == "Results":
                    channel = data.get("channel", {})
                    alternatives = channel.get("alternatives", [])
                    if not alternatives:
                        continue

                    transcript = alternatives[0].get("transcript", "")
                    is_final = data.get("is_final", False)
                    start = data.get("start", 0)
                    duration = data.get("duration", 0)

                    if is_final:
                        self._segment_counter += 1
                        await self._queue.put(SttEvent(
                            kind="final",
                            id=f"seg_{self._segment_counter}",
                            text=transcript,
                            t_start_ms=int(start * 1000),
                            t_end_ms=int((start + duration) * 1000),
                            lang=self.lang,
                        ))
                    elif transcript:
                        self._segment_counter += 1
                        await self._queue.put(SttEvent(
                            kind="partial",
                            id=f"seg_{self._segment_counter}",
                            text=transcript,
                            t_ms=int(start * 1000),
                            lang=self.lang,
                        ))

                elif data.get("type") == "Error":
                    await self._queue.put(SttEvent(
                        kind="error",
                        message=data.get("message", "Deepgram error"),
                    ))
        except Exception as e:
            await self._queue.put(SttEvent(kind="error", message=str(e)))
        finally:
            await self._queue.put(SttEvent(kind="closed"))


class DeepgramSttProvider:
    """Deepgram STT provider factory."""

    name = "deepgram"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("DEEPGRAM_API_KEY", "")

    def supports(self, lang: str) -> bool:
        return lang in ("hi-IN", "en-IN", "auto")

    async def open(self, lang: str, sample_rate: int = 16000) -> SttSession:
        if not self.api_key:
            raise ValueError("Deepgram API key not configured")
        session = DeepgramSttSession(self.api_key, lang)
        await session._connect()
        return session