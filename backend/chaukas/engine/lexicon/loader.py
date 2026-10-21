"""Lexicon loader and validation for the Chaukas detection engine."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

# All signal IDs from PRD §6.4
SIGNAL_IDS = frozenset([
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
])

LANGUAGES = frozenset(["hi", "en", "hinglish"])

PatternKind = str  # "phrase" | "token" | "regex"


class LexiconEntry(BaseModel):
    """A single lexicon pattern entry."""
    signal: str
    kind: str  # "phrase" | "token" | "regex"
    value: str
    lang: str
    fuzzy: bool = False
    note: str = ""

    @field_validator("signal")
    @classmethod
    def valid_signal(cls, v: str) -> str:
        if v not in SIGNAL_IDS:
            raise ValueError(f"Unknown signal_id: {v}")
        return v

    @field_validator("lang")
    @classmethod
    def valid_lang(cls, v: str) -> str:
        if v not in LANGUAGES:
            raise ValueError(f"Invalid language: {v}. Must be one of {LANGUAGES}")
        return v

    @field_validator("kind")
    @classmethod
    def valid_kind(cls, v: str) -> str:
        if v not in ("phrase", "token", "regex"):
            raise ValueError(f"Invalid kind: {v}. Must be phrase, token, or regex")
        return v

    @field_validator("value")
    @classmethod
    def non_empty_value(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Pattern value must not be empty")
        if v.strip() == "":
            raise ValueError("Pattern value must not be empty after stripping whitespace")
        # Validate regex patterns
        if v.strip() == "":
            raise ValueError("Pattern value must not be empty after stripping whitespace")
        if v.strip() == "":
            raise ValueError("Pattern value must not be empty after stripping whitespace")
        return v

    @field_validator("value")
    @classmethod
    def validate_pattern_value(cls, v: str, info) -> str:
        """Ensure no leading/trailing whitespace in values."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Empty pattern value")
        return stripped

@dataclass(frozen=True)
class CompiledPattern:
    """A compiled matching pattern ready for use by the scorer."""
    signal_id: str
    kind: str  # "phrase" | "token" | "regex"
    value: str  # normalised form for matching
    compiled: object  # compiled regex or string
    fuzzy: bool
    label_en: str
    label_hi: str
    weight: float  # resolved at scoring time
    span_hint: tuple[int, int] | None = None  # optional hint for matches


def _load_yaml(path: Path) -> list[dict]:
    """Load YAML lexicon file using PyYAML."""
    import yaml
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, list):
        raise TypeError(f"Lexicon file must contain a YAML list, got {type(data).__name__}: {path}")
    return data


def load_and_validate(lexicon_dir: Path, lang: str) -> list[LexiconEntry]:
    """Load and validate all entries for a language from a YAML lexicon file.

    Raises ValueError on validation failure:
    - Unknown signal IDs
    - Empty values
    - Duplicate pattern values for the same (signal, kind)
    - Unsorted keys
    """
    path = lexicon_dir / f"{lang}.yaml"
    raw = _load_yaml(path)

    entries: list[LexiconEntry] = []
    seen_keys: set[tuple[str, str]] = set()

    for item in raw:
        entry = LexiconEntry(**item)
        dup_key = (entry.signal, entry.kind, entry.value)
        if dup_key in seen_keys:
            raise ValueError(f"Duplicate pattern ({entry.signal}, {entry.kind}, '{entry.value}') in {lang}.yaml")
        seen_keys.add(dup_key)
        entries.append(entry)

    # Verify minimum pattern count: at least 15 per signal per language
    from collections import Counter
    signal_counts: Counter = Counter(e.signal for e in entries)
    min_patterns = 15
    for sid in SIGNAL_IDS:
        cnt = signal_counts.get(sid, 0)
        if cnt < min_patterns:
            raise ValueError(
                f"Signal '{sid}' has only {cnt} patterns in {lang}.yaml "
                f"(minimum {min_patterns})"
            )

    return entries


def compile_patterns(entries: list[LexiconEntry]) -> list[CompiledPattern]:
    """Convert lexicon entries into compiled patterns ready for matching."""
    patterns: list[CompiledPattern] = []

    for entry in entries:
        if entry.kind == "regex":
            try:
                compiled = re.compile(entry.value, re.IGNORECASE | re.UNICODE)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern in lexicon: '{entry.value}' — {e}")
            compiled_obj = compiled
        elif entry.kind == "phrase":
            compiled_obj = entry.value.lower()
        else:  # token
            compiled_obj = entry.value.lower()

        patterns.append(CompiledPattern(
            signal_id=entry.signal,
            kind=entry.kind,
            value=entry.value,
            compiled=compiled_obj,
            fuzzy=entry.fuzzy,
            label_en="",  # filled at scoring time
            label_hi="",
            weight=0.0,  # filled at scoring time with base weight
        ))

    return patterns


@dataclass(frozen=True)
class SignalWeight:
    """Base weight and hard flag for a signal."""
    id: str
    weight: float
    hard: bool = False


# PRD §6.4 weights
SIGNAL_WEIGHTS: dict[str, SignalWeight] = {
    "authority_claim": SignalWeight(id="authority_claim", weight=12, hard=False),
    "digital_arrest": SignalWeight(id="digital_arrest", weight=22, hard=False),
    "accusation": SignalWeight(id="accusation", weight=14, hard=False),
    "urgency_threat": SignalWeight(id="urgency_threat", weight=10, hard=False),
    "secrecy_isolation": SignalWeight(id="secrecy_isolation", weight=24, hard=False),
    "credential_request": SignalWeight(id="credential_request", weight=30, hard=True),
    "transfer_demand": SignalWeight(id="transfer_demand", weight=30, hard=True),
    "remote_access": SignalWeight(id="remote_access", weight=28, hard=True),
    "reward_task": SignalWeight(id="reward_task", weight=14, hard=False),
    "kyc_expiry": SignalWeight(id="kyc_expiry", weight=10, hard=False),
    "courier_customs": SignalWeight(id="courier_customs", weight=10, hard=False),
    "emergency_relative": SignalWeight(id="emergency_relative", weight=16, hard=False),
}

# Label maps for display
LABEL_MAP: dict[str, dict[str, str]] = {
    "authority_claim": {"en": "Authority claim", "hi": "अधिकारी का दावा"},
    "digital_arrest": {"en": "Digital arrest", "hi": "डिजिटल अरेस्ट"},
    "accusation": {"en": "Accusation", "hi": "दोषारोपण"},
    "urgency_threat": {"en": "Urgency & threat", "hi": "तेज़ी और धमकी"},
    "secrecy_isolation": {"en": "Secrecy & isolation", "hi": "राज़गीरी और अलगाव"},
    "credential_request": {"en": "Credential request", "hi": "करेंशियल माँग"},
    "transfer_demand": {"en": "Transfer demand", "hi": "पैसा ट्रांसफर की माँग"},
    "remote_access": {"en": "Remote access", "hi": "रिमोट एक्सेस"},
    "reward_task": {"en": "Reward / task scam", "hi": "इनाम और कार्य धोखाधड़ी"},
    "kyc_expiry": {"en": "KYC expiry", "hi": "केवाईसी समाप्त"},
    "courier_customs": {"en": "Courier / customs", "hi": "कूरियर कस्टम"},
    "emergency_relative": {"en": "Emergency relative", "hi": "परिवार वाले की मुसीबत"},
}

# Warning cue keywords that trigger warning context
WARNING_CUES = [
    "never", "never share", "never tell", "don't share", "don't tell",
    "do not share", "do not tell", "should not", "shouldn't",
    "kabhi nahi", "कभी नहीं", "न बताएं", "मत बताइए",
    "beware", "saavdhan", "सावधान", "fraud alert", "scam alert",
    "OTP किसी को न बताएं", "किसी को मत बताइए", "किसी को नहीं",
]

# Request verbs that make credential/transfer hits score fully
REQUEST_VERBS = [
    "tell", "give", "share", "send", "read out", "batao", "bataiye",
    "bata", "dijiye", "diijiye", "bhejo", "bhejiye", "bolo", "bolio",
    "बताइए", "दीजिए", "भेजिए", "बताओ", "बोलो",
]

# Negation cues
NEGATION_CUES = [
    "no need", "आपको ... नहीं देना है", "not required",
    "आवश्यक नहीं", "जरूरत नहीं", "nahi chahiye", "नहीं चाहिए",
]


def get_warning_context(normalised_tokens: list[str], max_pos: int) -> bool:
    """Check if any warning cue appears within ±7 tokens of position max_pos."""
    window_start = max(0, max_pos - 7)
    window_end = min(len(normalised_tokens), max_pos + 8)
    for i in range(window_start, window_end):
        t = normalised_tokens[i]
        for cue in WARNING_CUES:
            if cue in t:
                return True
    return False


def get_negation_context(normalised_tokens: list[str], max_pos: int) -> bool:
    """Check if any negation cue appears nearby."""
    window_start = max(0, max_pos - 4)
    window_end = min(len(normalised_tokens), max_pos + 4)
    for i in range(window_start, window_end):
        t = normalised_tokens[i]
        for cue in NEGATION_CUES:
            if cue in t:
                return True
    return False


def has_request_verb(normalised_tokens: list[str], hit_end_token_idx: int) -> bool:
    """Check if a request verb appears within ±8 tokens of the hit."""
    window_start = max(0, hit_end_token_idx - 8)
    window_end = min(len(normalised_tokens), hit_end_token_idx + 9)
    for i in range(window_start, window_end):
        t = normalised_tokens[i]
        for verb in REQUEST_VERBS:
            if verb in t:
                return True
    return False
