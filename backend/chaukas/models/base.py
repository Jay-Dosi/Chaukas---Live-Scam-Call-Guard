"""Shared pydantic models for the Chaukas wire protocol."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Level(str, Enum):
    """Risk levels."""
    CALM = "calm"
    CAUTION = "caution"
    DANGER = "danger"
    CRITICAL = "critical"


class Speaker(str, Enum):
    """Speaker roles."""
    CALLER = "caller"
    USER = "user"
    UNKNOWN = "unknown"


SignalId = Literal[
    "authority_claim",
    "digital_arrest",
    "accusation",
    "urgency_threat",
    "secrecy_isolation",
    "credential_request",
    "transfer_demand",
    "remote_access",
    "reward_task",
    "kyc_expiry",
    "courier_customs",
    "emergency_relative",
]


ContextType = Literal["asserted", "warning", "negated"]


class Segment(BaseModel):
    """A transcript segment from STT."""
    id: str
    text: str
    is_final: bool
    t_start_ms: int
    t_end_ms: int
    lang: str | None = None
    speaker: Speaker = Speaker.UNKNOWN


class SignalHit(BaseModel):
    """A single lexicon match."""
    signal_id: SignalId
    label_en: str
    label_hi: str
    weight: float
    hard: bool
    matched: str
    segment_id: str
    span_start: int
    span_end: int
    t_ms: int
    context: ContextType


class Combo(BaseModel):
    """A detected tactic combination."""
    id: str
    bonus: float


class LlmAssessment(BaseModel):
    """Optional LLM classification result."""
    scam_probability: float = Field(..., ge=0, le=1)
    tactics: list[SignalId]
    reason_en: str
    reason_hi: str
    is_likely_genuine: bool


class Analysis(BaseModel):
    """Result of analysis after ingesting segments."""
    score: int = Field(..., ge=0, le=100)
    level: Level
    hits: list[SignalHit] = []
    combos: list[Combo] = []
    reason_en: str
    reason_hi: str
    next_advice_en: str
    next_advice_hi: str
    t_ms: int
    llm_applied: bool = False


class EngineState(BaseModel):
    """Serializable engine snapshot for serialization between sessions."""
    hits: list[SignalHit]
    score: int
    level: Level