"""Explanation generation for Chaukas detection engine.

Generates plain-language reasons and advice in English and Hindi.
"""

from __future__ import annotations

from chaukas.engine.scorer import ActiveHit, ScorerState
from chaukas.models.base import Analysis, Level, SignalHit


def generate_explanation(analysis: Analysis) -> tuple[str, str]:
    """Generate human-readable explanation for the analysis.

    Returns (reason_en, reason_hi)
    """
    if not analysis.hits:
        return "Nothing suspicious so far.", "अभी तक कुछ शक नहीं है।"

    return analysis.reason_en, analysis.reason_hi


def generate_advice(analysis: Analysis) -> tuple[str, str]:
    """Generate next-step advice for the user.

    Returns (advice_en, advice_hi)
    """
    return analysis.next_advice_en, analysis.next_advice_hi


def format_alert_text(level: Level, lang: str = "en") -> str:
    """Get the alert text for a level in the given language."""
    from chaukas.engine.alerts import ALERTS

    alert = ALERTS.get(level)
    if not alert:
        return ""

    if lang == "hi":
        return alert.hi
    return alert.en


def describe_hits(hits: list[SignalHit]) -> list[dict]:
    """Convert hits to serializable dicts for display."""
    return [
        {
            "signal_id": h.signal_id,
            "label_en": h.label_en,
            "label_hi": h.label_hi,
            "weight": round(h.weight, 1),
            "hard": h.hard,
            "matched": h.matched,
            "context": h.context,
            "segment_id": h.segment_id,
            "span_start": h.span_start,
            "span_end": h.span_end,
            "t_ms": h.t_ms,
        }
        for h in hits
    ]


def describe_combos(combos: list) -> list[dict]:
    """Convert combos to serializable dicts for display."""
    return [{"id": c.id, "bonus": c.bonus} for c in combos]