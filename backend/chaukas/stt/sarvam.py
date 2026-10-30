"""Sarvam AI STT adapter — PRD §8.5.

Implemented against Sarvam's current official streaming API docs.
Uses WebSocket streaming with appropriate auth and audio format.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import time
from typing import AsyncIterator

import websockets
from websockets.client import WebSocketClientProtocol

from chaukas.stt.base import SttEvent, SttProvider, SttSession


class SarvamSttSession:
    """Sarvam streaming STT session."""

    def __init__(self, api_key: str, lang: str):
        self.api_key = api_key
        self.lang = self._map_lang(lang)
        self._start_time = time.time()
        self._ws: WebSocketClientProtocol | None = None
        self._queue: asyncio.Queue[SttEvent] = asyncio.Queue()
        self._receive_task: asyncio.Task | None = None
        self._segment_counter = 0

    def _map_lang(self, lang: str) -> str:
        if not lang or lang == "auto":
            return "auto"
        if lang.startswith("hi"):
            return "hi-IN"
        if lang.startswith("en"):
            return "en-IN"
        return "auto"

    @property
    def _is_connected(self) -> bool:
        if not self._ws:
            return False
        if hasattr(self._ws, "closed"):
            return not self._ws.closed
        if hasattr(self._ws, "state"):
            return getattr(self._ws.state, "name", "") == "OPEN"
        return True

    async def push(self, pcm16: bytes) -> None:
        if self._is_connected:
            # Sarvam expects base64-encoded PCM16 in audio_input event
            audio_b64 = base64.b64encode(pcm16).decode("ascii")
            try:
                await self._ws.send(json.dumps({"event": "audio_input", "audio": audio_b64}))
            except Exception:
                pass

    async def stop(self) -> None:
        if self._ws:
            try:
                await self._ws.send(json.dumps({"event": "end"}))
            except Exception:
                pass
            try:
                await self._ws.close()
            except Exception:
                pass
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
        """Establish WebSocket connection to Sarvam realtime streaming STT."""
        url = f"wss://api.sarvam.ai/speech-to-text-realtime/ws?language_code={self.lang}&model=saaras:v3-realtime&stream_type=fast"
        headers = {
            "api-subscription-key": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            self._ws = await websockets.connect(url, additional_headers=headers)
        except TypeError:
            self._ws = await websockets.connect(url, additional_headers=headers)

        # Start receive loop
        self._receive_task = asyncio.create_task(self._receive_loop())

    async def _receive_loop(self) -> None:
        """Process incoming WebSocket messages."""
        try:
            async for message in self._ws:
                data = json.loads(message)
                event_type = data.get("event") or data.get("type") or ""

                now_ms = int((time.time() - self._start_time) * 1000)

                if event_type in ("transcript.partial", "partial"):
                    text = data.get("text") or data.get("transcript") or ""
                    if text.strip():
                        utt_idx = data.get("utterance_idx", self._segment_counter)
                        seg_id = f"utt_{utt_idx}"
                        start_s = data.get("start_s") or data.get("timestamp")
                        t_ms = int(start_s * 1000) if isinstance(start_s, (int, float)) and start_s < 10000 else (int(start_s) if start_s else now_ms)
                        await self._queue.put(SttEvent(
                            kind="partial",
                            id=seg_id,
                            text=text,
                            t_ms=t_ms,
                            lang=data.get("language", self.lang),
                        ))
                elif event_type in ("transcript.final", "transcript", "final"):
                    text = data.get("text") or data.get("transcript") or ""
                    if text.strip():
                        utt_idx = data.get("utterance_idx", self._segment_counter)
                        seg_id = f"utt_{utt_idx}"
                        self._segment_counter += 1
                        start_s = data.get("start_s") or data.get("start_timestamp")
                        end_s = data.get("end_s") or data.get("end_timestamp")
                        t_start = int(start_s * 1000) if isinstance(start_s, (int, float)) and start_s < 10000 else (int(start_s) if start_s else max(0, now_ms - 1000))
                        t_end = int(end_s * 1000) if isinstance(end_s, (int, float)) and end_s < 10000 else (int(end_s) if end_s else now_ms)
                        await self._queue.put(SttEvent(
                            kind="final",
                            id=seg_id,
                            text=text,
                            t_start_ms=t_start,
                            t_end_ms=t_end,
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