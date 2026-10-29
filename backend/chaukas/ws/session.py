"""WebSocket session handler — PRD §8.2.

One TaskGroup per socket, bounded audio queue with backpressure,
idle timeout, session cap, pydantic validation, STT reconnect with backoff.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from chaukas.config import get_settings
from chaukas.engine.engine import Engine
from chaukas.llm.assess import LlmAssessor
from chaukas.models.base import Segment, Speaker
from chaukas.stt.base import SttEvent
from chaukas.stt.registry import get_stt_provider
from chaukas.ws.protocol import (
    ClientMessage,
    ClientStart,
    client_message_adapter,
    ReadyEvent,
    PartialEvent,
    FinalEvent,
    AnalysisEvent,
    AlertEvent,
    ProgressEvent,
    SummaryEvent,
    ErrorEvent,
    ClosedEvent,
)

logger = logging.getLogger(__name__)
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
        self.transcript_history: list[dict] = []

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
    ctx: SessionContext | None = None

    try:
        # First message must be start
        start_data = None
        while True:
            msg = await websocket.receive()
            if msg.get("type") == "websocket.disconnect":
                return
            if "text" in msg:
                try:
                    start_data = ClientStart.model_validate_json(msg["text"])
                    break
                except ValidationError as e:
                    await websocket.send_json(ErrorEvent(code="invalid_start", message=str(e)).model_dump())
                    await websocket.close()
                    return
            # Ignore stray binary audio frames received before start

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
        if ctx is not None:
            await _cleanup(ctx)


async def _init_stt(ctx: SessionContext):
    """Initialize STT session."""
    try:
        lang = ctx.lang if ctx.lang != "auto" else "hi-IN"
        ctx.stt_session = await ctx.stt_provider.open(lang, 16000)
    except Exception as e:
        logger.warning(f"STT init failed: {e}")


async def _receive_loop(ctx: SessionContext):
    """Handle incoming client messages."""
    ws = ctx.websocket

    while True:
        try:
            msg = await ws.receive()
            ctx.mark_activity()

            if "text" in msg:
                data = client_message_adapter.validate_json(msg["text"])
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
        seg = Segment(
            id=msg.id,
            text=msg.text,
            is_final=msg.is_final,
            t_start_ms=msg.t_ms,
            t_end_ms=msg.t_ms + 1000,
            lang=ctx.lang if ctx.lang != "auto" else None,
            speaker=Speaker.UNKNOWN,
        )
        ctx.transcript_history.append({"text": msg.text, "t_ms": msg.t_ms, "is_final": msg.is_final})
        analysis = ctx.engine.ingest(seg)
        await _push_analysis(ctx, analysis)

    elif msg.type == "mute":
        ctx.mute_until_ms = int(time.time() * 1000) + msg.ms

    elif msg.type == "chip":
        pass

    elif msg.type == "stop":
        await ctx.websocket.close()


async def _handle_audio_frame(ctx: SessionContext, pcm16: bytes):
    """Queue audio frame with backpressure and forward to STT."""
    now_ms = int(time.time() * 1000)
    if now_ms < ctx.mute_until_ms:
        return

    try:
        ctx.audio_queue.put_nowait(pcm16)
        if ctx.stt_session:
            await ctx.stt_session.push(pcm16)
    except asyncio.QueueFull:
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
            seg_id = event.id or str(uuid.uuid4())[:8]
            t_ms = event.t_ms or 0
            await ctx.websocket.send_json(PartialEvent(
                type="partial", id=seg_id, text=event.text or "", t_ms=t_ms
            ).model_dump())

            # Ingest partial into engine so risk score and tactics update in real-time
            if event.text and (int(time.time() * 1000) > ctx.mute_until_ms):
                seg = Segment(
                    id=seg_id,
                    text=event.text,
                    is_final=False,
                    t_start_ms=t_ms,
                    t_end_ms=t_ms + 1000,
                    lang=event.lang or (ctx.lang if ctx.lang != "auto" else None),
                    speaker=Speaker.UNKNOWN,
                )
                analysis = ctx.engine.ingest(seg)
                await _push_analysis(ctx, analysis)

        elif event.kind == "final":
            seg_id = event.id or str(uuid.uuid4())[:8]
            t_start = event.t_start_ms or 0
            t_end = event.t_end_ms or t_start + 1000

            await ctx.websocket.send_json(FinalEvent(
                type="final", id=seg_id, text=event.text or "",
                t_start_ms=t_start, t_end_ms=t_end, lang=event.lang
            ).model_dump())

            # Ingest into engine if text is present and outside mute window
            if event.text and (int(time.time() * 1000) > ctx.mute_until_ms):
                seg = Segment(
                    id=seg_id,
                    text=event.text,
                    is_final=True,
                    t_start_ms=t_start,
                    t_end_ms=t_end,
                    lang=event.lang or (ctx.lang if ctx.lang != "auto" else None),
                    speaker=Speaker.UNKNOWN,
                )
                ctx.transcript_history.append({"text": event.text, "t_ms": t_start, "is_final": True})
                analysis = ctx.engine.ingest(seg)
                await _push_analysis(ctx, analysis)

        elif event.kind == "error":
            await ctx.websocket.send_json(ErrorEvent(
                code="stt_error", message=event.message or "STT error"
            ).model_dump())
            await _stt_reconnect(ctx)

        elif event.kind == "closed":
            break


async def _stt_reconnect(ctx: SessionContext):
    """Reconnect STT with exponential backoff (max 3 tries)."""
    for attempt in range(3):
        await asyncio.sleep(2 ** attempt)
        try:
            if ctx.stt_session:
                await ctx.stt_session.stop()
        except Exception:
            pass
        try:
            lang = ctx.lang if ctx.lang != "auto" else "hi-IN"
            ctx.stt_session = await ctx.stt_provider.open(lang, 16000)
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
        lvl_str = analysis.level.value if hasattr(analysis.level, "value") else str(analysis.level)
        await ctx.websocket.send_json(AlertEvent(
            type="alert",
            level=lvl_str,
            text_en=alert_text,
            text_hi=alert_hi or "",
            cooldown_ms=mute_ms or 0,
        ).model_dump())


async def _llm_assessor_loop(ctx: SessionContext):
    """Periodically call LLM assessor when risk rises or new speech accumulates."""
    last_tokens_count = 0
    while True:
        await asyncio.sleep(6)
        if ctx.is_expired or ctx.is_idle:
            break

        if not ctx.transcript_history:
            continue

        full_text = " ".join(t["text"] for t in ctx.transcript_history[-15:])
        token_count = len(full_text.split())

        # Check conditions from PRD §6.6
        current_lvl = ctx.engine._scorer.last_level
        lvl_qualifies = current_lvl in ("caution", "danger", "critical")
        tokens_qualify = (token_count - last_tokens_count) >= 40

        if lvl_qualifies or tokens_qualify:
            last_tokens_count = token_count
            hard_floor = ctx.engine._hard_floor()
            rule_score = ctx.engine._scorer_state_score()
            assessment = await ctx.llm_assessor.assess(full_text, ctx.lang, rule_score, hard_floor)
            if assessment:
                analysis = ctx.engine.apply_assessment(assessment, int(time.time() * 1000))
                await _push_analysis(ctx, analysis)


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
    """Pacing for inject and upload modes."""
    try:
        turns: list[dict] = []
        expected_tactics: list[str] = []

        if ctx.mode == "inject":
            if ctx.case_id:
                corpus_path = Path(__file__).resolve().parent.parent / "corpus" / f"{ctx.case_id}.json"
                if corpus_path.exists():
                    with open(corpus_path, encoding="utf-8") as f:
                        cdata = json.load(f)
                        turns = cdata.get("turns", [])
                        expected_tactics = cdata.get("tactics", [])
            elif ctx.scenario_id:
                from chaukas.drill.machine import load_scenario
                try:
                    sc = load_scenario(ctx.scenario_id, ctx.lang)
                    expected_tactics = sc.tactics
                    curr = sc.start
                    visited = set()
                    while curr and curr not in visited and curr in sc.nodes:
                        visited.add(curr)
                        node = sc.nodes[curr]
                        turns.append({"speaker": "caller", "text": node.text, "tMs": len(turns) * 3000})
                        next_id = None
                        for t in node.next:
                            if not t["to"].startswith("END_"):
                                next_id = t["to"]
                                break
                        curr = next_id
                except Exception as e:
                    logger.warning(f"Error loading scenario for inject: {e}")

        elif ctx.mode == "upload":
            from chaukas.api.upload import UPLOAD_JOBS
            if ctx.job_id and ctx.job_id in UPLOAD_JOBS:
                pcm_path = UPLOAD_JOBS[ctx.job_id]
                if ctx.stt_session and Path(pcm_path).exists():
                    from chaukas.audio.decode import stream_pcm
                    speed = min(4.0, max(1.0, ctx.speed))
                    async for chunk, t_ms in stream_pcm(pcm_path, chunk_ms=100, speed=speed):
                        await ctx.stt_session.push(chunk)
                        await asyncio.sleep(0.025 / speed)
                    return

        if not turns:
            corpus_files = list((Path(__file__).resolve().parent.parent / "corpus").glob("s-*.json"))
            if corpus_files:
                with open(corpus_files[0], encoding="utf-8") as f:
                    cdata = json.load(f)
                    turns = cdata.get("turns", [])
                    expected_tactics = cdata.get("tactics", [])

        if not turns:
            return

        peak_score = 0
        peak_level = "calm"
        time_to_caution = None
        time_to_danger = None
        time_to_critical = None
        detected_tactics: set[str] = set()

        speed = max(0.5, min(4.0, ctx.speed))
        total_turns = len(turns)

        for i, turn in enumerate(turns):
            if ctx.is_expired or ctx.is_idle:
                break

            text = turn["text"]
            t_ms = turn.get("tMs", i * 3000)

            # Emit partial
            seg_id = f"inj_{i}"
            words = text.split()
            partial_text = " ".join(words[:max(1, len(words) // 2)])
            await ctx.websocket.send_json(PartialEvent(
                type="partial", id=seg_id, text=partial_text, t_ms=t_ms
            ).model_dump())

            await asyncio.sleep(0.25 / speed)

            # Emit final
            await ctx.websocket.send_json(FinalEvent(
                type="final", id=seg_id, text=text,
                t_start_ms=t_ms, t_end_ms=t_ms + 2000, lang=ctx.lang
            ).model_dump())

            # Ingest segment
            seg = Segment(
                id=seg_id,
                text=text,
                is_final=True,
                t_start_ms=t_ms,
                t_end_ms=t_ms + 2000,
                lang=ctx.lang if ctx.lang != "auto" else None,
                speaker=Speaker.CALLER,
            )
            analysis = ctx.engine.ingest(seg)
            await _push_analysis(ctx, analysis)

            if analysis.score > peak_score:
                peak_score = analysis.score
                peak_level = analysis.level.value if hasattr(analysis.level, "value") else str(analysis.level)

            lvl = analysis.level.value if hasattr(analysis.level, "value") else str(analysis.level)
            if lvl in ("caution", "danger", "critical") and time_to_caution is None:
                time_to_caution = t_ms
            if lvl in ("danger", "critical") and time_to_danger is None:
                time_to_danger = t_ms
            if lvl == "critical" and time_to_critical is None:
                time_to_critical = t_ms

            for hit in analysis.hits:
                detected_tactics.add(hit.signal_id)

            pct = round((i + 1) / total_turns, 2)
            await ctx.websocket.send_json(ProgressEvent(type="progress", pct=pct).model_dump())

            await asyncio.sleep(1.0 / speed)

        # Emit summary
        missed = [t for t in expected_tactics if t not in detected_tactics]
        await ctx.websocket.send_json(SummaryEvent(
            type="summary",
            duration_secs=int((total_turns * 3) / speed),
            peak_level=peak_level,
            peak_score=peak_score,
            time_to_caution=time_to_caution,
            time_to_danger=time_to_danger,
            time_to_critical=time_to_critical,
            final_score=peak_score,
            expected_tactics=expected_tactics,
            detected_tactics=sorted(list(detected_tactics)),
            missed_tactics=sorted(missed),
        ).model_dump())

    except Exception as e:
        logger.error(f"Error in pacing task: {e}")


async def _cleanup(ctx: SessionContext):
    """Clean up session resources."""
    for task in ctx._tasks:
        task.cancel()

    if ctx.stt_session:
        try:
            await ctx.stt_session.stop()
        except Exception:
            pass

    try:
        await ctx.websocket.send_json(ClosedEvent(type="closed").model_dump())
        await ctx.websocket.close()
    except Exception:
        pass