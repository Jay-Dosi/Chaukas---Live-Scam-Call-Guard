"""WebSocket protocol models — PRD §8.2.

All client/server message types as pydantic models.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ─── Client → Server ───

class ClientStart(BaseModel):
    type: Literal["start"]
    mode: Literal["live", "inject", "upload", "drill"]
    lang: Literal["hi-IN", "en-IN", "auto"]
    sensitivity: Literal["standard", "high"]
    sample_rate: int = 16000
    scenario_id: str | None = None
    case_id: str | None = None
    job_id: str | None = None
    speed: float = Field(default=1.0, le=4.0)
    noise_wer: float = Field(default=0.0, ge=0.0, le=0.4)
    fixture_id: str | None = None


class ClientText(BaseModel):
    type: Literal["text"]
    id: str
    text: str
    is_final: bool
    t_ms: int


class ClientMute(BaseModel):
    type: Literal["mute"]
    ms: int


class ClientChip(BaseModel):
    type: Literal["chip"]
    act: Literal["comply", "question", "verify", "refuse"]


class ClientStop(BaseModel):
    type: Literal["stop"]


ClientMessage = ClientStart | ClientText | ClientMute | ClientChip | ClientStop


# ─── Server → Client ───

class ReadyEvent(BaseModel):
    type: Literal["ready"]
    providers: dict


class PartialEvent(BaseModel):
    type: Literal["partial"]
    id: str
    text: str
    t_ms: int


class FinalEvent(BaseModel):
    type: Literal["final"]
    id: str
    text: str
    t_start_ms: int
    t_end_ms: int
    lang: str | None


class AnalysisEvent(BaseModel):
    type: Literal["analysis"]
    analysis: dict  # Analysis model


class AlertEvent(BaseModel):
    type: Literal["alert"]
    level: str
    text_en: str
    text_hi: str
    cooldown_ms: int


class CallerEvent(BaseModel):
    type: Literal["caller"]
    node_id: str
    text: str
    tactics: list[str]
    audio_url: str | None
    pressure: int


class DrillEndEvent(BaseModel):
    type: Literal["ended"]
    outcome: Literal["safe", "unsafe"]
    scorecard: dict
    debrief: dict


class ProgressEvent(BaseModel):
    type: Literal["progress"]
    pct: float


class SummaryEvent(BaseModel):
    type: Literal["summary"]
    duration_secs: int
    peak_level: str
    peak_score: int
    time_to_caution: int | None
    time_to_danger: int | None
    time_to_critical: int | None
    final_score: int
    expected_tactics: list[str]
    detected_tactics: list[str]
    missed_tactics: list[str]


class ErrorEvent(BaseModel):
    type: Literal["error"]
    code: str
    message: str


class ClosedEvent(BaseModel):
    type: Literal["closed"]


ServerEvent = (
    ReadyEvent
    | PartialEvent
    | FinalEvent
    | AnalysisEvent
    | AlertEvent
    | CallerEvent
    | DrillEndEvent
    | ProgressEvent
    | SummaryEvent
    | ErrorEvent
    | ClosedEvent
)