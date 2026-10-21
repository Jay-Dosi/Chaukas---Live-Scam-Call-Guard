"""WebSocket session handler — PRD §8.2.

One TaskGroup per socket, bounded audio queue with backpressure,
idle timeout, session cap, pydantic validation, STT reconnect with backoff.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from chaukas.config import get_settings
from chaukas.engine.engine import Engine
from chaukas.llm.assess import LlmAssessor
from chaukas.stt.base import SttEvent
from chaukas.stt.registry import get_stt_provider
from chaukas.ws.protocol import (
    ClientMessage,
    ClientStart,
    ReadyEvent,
    PartialEvent,
    FinalEvent,
    AnalysisEvent,
    AlertEvent,
    ErrorEvent,
    ClosedEvent,
)

settings = get_settings()

MAX_SESSION_MS = settings.max_session_minutes * 60 * 1000
IDLE_TIMEOUT_MS = 60 * 1000  # 60 seconds
AUDIO_QUEUE_MAX_MS = 2000  # 2 seconds buffered
MUTE_WINDOW_MS = 300


class SessionContext:
    """Per-session state."""

    def __init__(self, websocket: WebSocket, start_msg: ClientStart):
        self.websocket = websocket
        self.mode = start_msg.mode
        self.lang = start_msg.lang
        self.sensitivity = start_msg.sensitivity
        self.scenario_id = start_msg.scenario_id
        self.case_id = start_msg.case_id
        self.job_id = start_msg.job_id
        self.speed = start_msg.speed
        self.noise_wer = start_msg.noise_wer
        self.fixture_id = start_msg.fixture_id

        self.engine = Engine(sensitivity=start_msg.sensitivity)
        self.llm_assessor = LlmAssessor()
        self.session_id = str(uuid.uuid4())[:8]
        self.start_ms = int(time.time() * 1000)
        self.last_activity_ms = self.start_ms

        # Audio queue with backpressure
        self.audio_queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=100)
        self.mute_until_ms = 0

        # STT
        self.stt_provider = get_stt_provider()
        self.stt_session = None
        self._stt_task = None

        # Tasks
        self._tasks: set[asyncio.Task] = set()

    @property
    def elapsed_ms(self) -> int:
        return int(time.time() * 1000) - self.start_ms

    @property
    def is_idle(self) -> bool:
        return (int(time.time() * 1000) - self.last_activity_ms) > IDLE_TIMEOUT_MS

    @property
    def is_expired(self) -> bool:
        return self.elapsed_ms > MAX_SESSION_MS

    def mark_activity(self):
        self.last_activity_ms = int(time.time() * 1000)


async def handle_session(websocket: WebSocket):
    """Main WebSocket session handler."""
    await websocket.accept()

    try:
        # First message must be start
        raw = await websocket.receive_text()
        try:
            start_data = ClientStart.model_validate_json(raw)
        except ValidationError as e:
            await websocket.send_json(ErrorEvent(code="invalid_start", message=str(e)).model_dump())
            await websocket.close()
            return

        ctx = SessionContext(websocket, start_data)

        # Initialize STT
        await _init_stt(ctx)

        # Send ready
        await websocket.send_json(ReadyEvent(
            type="ready",
            providers={
                "stt": ctx.stt_provider.name,
                "engine": "rules",
                "llm": ctx.llm_assessor.enabled,
            }
        ).model_dump())

        # Run main loops
        async with asyncio.TaskGroup() as tg:
            ctx._tasks = tg._tasks  # type: ignore

            # Receive loop
            tg.create_task(_receive_loop(ctx))

            # STT event pump
            if ctx.stt_session:
                tg.create_task(_stt_event_pump(ctx))

            # LLM assessor (periodic)
            if ctx.llm_assessor.enabled:
                tg.create_task(_llm_assessor_loop(ctx))

            # Idle/session timeout monitor
            tg.create_task(_timeout_monitor(ctx))

            # Mode-specific pacing
            if ctx.mode in ("inject", "upload"):
                tg.create_task(_pacing_task(ctx))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json(ErrorEvent(code="server_error", message=str(e)).model_dump())
        except Exception:
            pass
    finally:
        await _cleanup(ctx)


async def _init_stt(ctx: SessionContext):
    """Initialize STT session."""
    try:
        lang = ctx.lang if ctx.lang != "auto" else "hi-IN"
        ctx.stt_session = await ctx.stt_provider.open(lang, 16000)
    except Exception as e:
        # Log but continue — mock will handle
        print(f"STT init failed: {e}")


async def _receive_loop(ctx: SessionContext):
    """Handle incoming client messages."""
    ws = ctx.websocket

    while True:
        try:
            msg = await ws.receive()
            ctx.mark_activity()

            if "text" in msg:
                data = ClientMessage.model_validate_json(msg["text"])
                await _handle_client_message(ctx, data)
            elif "bytes" in msg:
                # Audio frame
                if ctx.mode in ("live", "drill"):
                    await _handle_audio_frame(ctx, msg["bytes"])
        except WebSocketDisconnect:
            break
        except ValidationError as e:
            await ws.send_json(ErrorEvent(code="validation_error", message=str(e)).model_dump())
        except Exception as e:
            await ws.send_json(ErrorEvent(code="message_error", message=str(e)).model_dump())


async def _handle_client_message(ctx: SessionContext, msg: ClientMessage):
    """Process validated client message."""
    if msg.type == "text":
        # Browser Web Speech fallback
        segment = ctx.engine.ingest_text(msg.text, msg.is_final, msg.t_ms)
        await _push_analysis(ctx, segment)

    elif msg.type == "mute":
        ctx.mute_until_ms = int(time.time() * 1000) + msg.ms

    elif msg.type == "chip":
        # Fire-Drill chip response
        await _handle_drill_chip(ctx, msg.act)

    elif msg.type == "stop":
        await ctx.websocket.close()


async def _handle_audio_frame(ctx: SessionContext, pcm16: bytes):
    """Queue audio frame with backpressure."""
    # Check mute window
    now_ms = int(time.time() * 1000)
    if now_ms < ctx.mute_until_ms:
        return

    try:
        ctx.audio_queue.put_nowait(pcm16)
    except asyncio.QueueFull:
        # Drop oldest and warn
        try:
            ctx.audio_queue.get_nowait()
            await ctx.websocket.send_json(ErrorEvent(
                code="backpressure",
                message="Audio buffer full, dropped oldest frame"
            ).model_dump())
        except Exception:
            pass


async def _stt_event_pump(ctx: SessionContext):
    """Forward STT events to client and engine."""
    if not ctx.stt_session:
        return

    async for event in ctx.stt_session.events():
        if event.kind == "partial":
            await ctx.websocket.send_json(PartialEvent(
                type="partial", id=event.id, text=event.text, t_ms=event.t_ms or 0
            ).model_dump())

        elif event.kind == "final":
            await ctx.websocket.send_json(FinalEvent(
                type="final", id=event.id, text=event.text,
                t_start_ms=event.t_start_ms or 0, t_end_ms=event.t_end_ms or 0, lang=event.lang
            ).model_dump())

            # Ingest into engine
            if event.text and (int(time.time() * 1000) > ctx.mute_until_ms):
                segment = ctx.engine.ingest(event.text, True, event.t_start_ms or 0, event.t_end_ms or 0)
                await _push_analysis(ctx, segment)

        elif event.kind == "error":
            await ctx.websocket.send_json(ErrorEvent(
                code="stt_error", message=event.message or "STT error"
            ).model_dump())

            # Attempt reconnect with backoff
            await _stt_reconnect(ctx)

        elif event.kind == "closed":
            break


async def _stt_reconnect(ctx: SessionContext):
    """Reconnect STT with exponential backoff (max 3 tries)."""
    for attempt in range(3):
        await asyncio.sleep(2 ** attempt)
        try:
            await ctx.stt_session.stop()
        except Exception:
            pass
        try:
            ctx.stt_session = await ctx.stt_provider.open(ctx.lang, 16000)
            await ctx.websocket.send_json(ErrorEvent(
                code="stt_reconnected", message="STT reconnected"
            ).model_dump())
            return
        except Exception:
            continue


async def _push_analysis(ctx: SessionContext, analysis):
    """Send analysis to client and check for alerts."""
    await ctx.websocket.send_json(AnalysisEvent(type="analysis", analysis=analysis.model_dump()).model_dump())

    # Check for alert
    alert_text, mute_ms = ctx.engine.check_alert(analysis)
    if alert_text:
        alert_hi = ctx.engine.check_alert_hi(analysis)
        await ctx.websocket.send_json(AlertEvent(
            type="alert",
            level=analysis.level,
            text_en=alert_text,
            text_hi=alert_hi or "",
            cooldown_mute_ms=mute_ms or 0,
        ).model_dump())


async def _llm_assessor_loop(ctx: SessionContext):
    """Periodically call LLM assessor."""
    while True:
        await asyncio.sleep(6)
        if ctx.is_expired or ctx.is_idle:
            break

        # TODO: Get rolling transcript window and call LLM
        pass


async def _timeout_monitor(ctx: SessionContext):
    """Monitor for idle timeout and session expiry."""
    while True:
        await asyncio.sleep(10)
        if ctx.is_idle:
            await ctx.websocket.send_json(ErrorEvent(
                code="idle_timeout", message="Session idle, closing"
            ).model_dump())
            await ctx.websocket.close()
            break
        if ctx.is_expired:
            await ctx.websocket.send_json(ErrorEvent(
                code="session_expired", message="Max session time reached"
            ).model_dump())
            await ctx.websocket.close()
            break


async def _pacing_task(ctx: SessionContext):
    """Pacing for inject/upload modes."""
    # TODO: Implement scenario/corpus replay at accelerated speed
    pass


async def _handle_drill_chip(ctx: SessionContext, act: str):
    """Handle Fire-Drill chip response."""
    from chaukas.drill.machine import run_turn, DrillState
    from chaukas.drill.classify import UserAct

    # TODO: Maintain drill state and run turn
    pass


async def _cleanup(ctx: SessionContext):
    """Clean up session resources."""
    # Cancel all tasks
    for task in ctx._tasks:
        task.cancel()

    # Stop STT
    if ctx.stt_session:
        await ctx.stt_session.stop()

    # Close websocket
    try:
        await ctx.websocket.send_json(ClosedEvent(type="closed").model_dump())
        await ctx.websocket.close()
    except Exception:
        pass