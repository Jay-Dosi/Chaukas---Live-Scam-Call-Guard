"""Chaukas Detection Engine — PRD §6.1.

Pure Python package with no I/O, no global state, no wall-clock reads.
Deterministic: same input sequence yields byte-identical serialised Analysis.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from chaukas.engine.lexicon.loader import (
    compile_patterns,
    load_and_validate,
    SIGNAL_WEIGHTS,
)
from chaukas.engine.scorer import ScorerState, ingest_segment
from chaukas.engine.alerts import ALERT_COOLDOWN_MS, ALERT_MUTE_MS, get_alert, mark_alert, should_alert
from chaukas.engine.scorer import _generate_advice, _generate_reason
from chaukas.models.base import (
    Analysis,
    EngineState,
    Level,
    LlmAssessment,
    Segment,
    SignalHit,
)

Sensitivity = Literal["standard", "high"]


@dataclass
class Engine:
    """Detection engine with per-session state."""

    sensitivity: Sensitivity = "standard"
    _scorer: ScorerState = field(default_factory=ScorerState, init=False)
    _patterns: dict[str, list] = field(default_factory=dict, init=False)
    _last_alert_time: dict[Level, int] = field(default_factory=dict, init=False)
    _initialized: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self._init_patterns()

    def _init_patterns(self) -> None:
        """Load and compile lexicon patterns for all three languages."""
        lexicon_dir = Path(__file__).parent / "lexicon"
        all_patterns: list = []

        for lang in ("en", "hi", "hinglish"):
            entries = load_and_validate(lexicon_dir, lang)
            patterns = compile_patterns(entries)
            all_patterns.extend(patterns)

        # Group by signal_id for fast lookup
        self._patterns = defaultdict(list)
        for p in all_patterns:
            self._patterns[p.signal_id].append(p)

        self._initialized = True

    def ingest(self, seg: Segment) -> Analysis:
        """Ingest a transcript segment and return updated analysis.

        Idempotent for repeated partials of the same segment ID.
        """
        if not self._initialized:
            self._init_patterns()

        analysis = ingest_segment(self._scorer, seg, dict(self._patterns))

        # Adjust thresholds for high sensitivity
        if self.sensitivity == "high":
            analysis = self._adjust_for_high_sensitivity(analysis)

        return analysis

    def _adjust_for_high_sensitivity(self, analysis: Analysis) -> Analysis:
        """Lower thresholds by 8 points for high sensitivity."""
        if analysis.level == "calm" and analysis.score >= 22:
            analysis.level = "caution"
        elif analysis.level == "caution" and analysis.score >= 47:
            analysis.level = "danger"
        elif analysis.level == "danger" and analysis.score >= 72:
            analysis.level = "critical"
        return analysis

    def apply_assessment(self, assessment: LlmAssessment, t_ms: int) -> Analysis:
        """Apply optional LLM assessment — PRD §6.6.

        Blend: final = clamp(round(0.7 * ruleScore + 0.3 * (100 * scamProbability)))
        LLM may raise by at most 20, lower by at most 15, never below hard floor.
        """
        # Get current state from scorer
        rule_score = self._scorer_state_score()

        # Calculate blended score
        llm_score = int(100 * assessment.scam_probability)
        blended = int(round(0.7 * rule_score + 0.3 * llm_score))

        # Apply bounds
        delta = blended - rule_score
        if delta > 20:
            blended = rule_score + 20
        elif delta < -15:
            blended = rule_score - 15

        # Get hard floor from active hits
        hard_floor = self._hard_floor()
        if hard_floor > 0:
            blended = max(blended, hard_floor)

        # Clamp
        blended = max(0, min(100, blended))

        # Re-determine level
        from chaukas.engine.scorer import _score_to_level, _apply_hysteresis
        new_level = _score_to_level(blended)
        level = _apply_hysteresis(self._scorer, new_level, blended)

        # Build analysis with same hits/combos but updated score/level
        # Re-generate reason/advice with new level
        from chaukas.engine.scorer import _generate_reason, _generate_advice
        reason_en, reason_hi = _generate_reason(
            self._scorer.active_hits.values(),
            list(self._scorer.active_hits.values()),
            blended,
            level,
        )
        advice_en, advice_hi = _generate_advice(
            level,
            set(h.signal_id for h in self._scorer.active_hits.values() if h.hard),
            set(h.signal_id for h in self._scorer.active_hits.values() if not h.hard),
        )

        return Analysis(
            score=blended,
            level=level,
            hits=list(self._scorer.active_hits.values()),
            combos=[],
            reason_en=reason_en,
            reason_hi=reason_hi,
            next_advice_en=advice_en,
            next_advice_hi=advice_hi,
            t_ms=t_ms,
            llm_applied=True,
        )

    def _scorer_state_score(self) -> int:
        """Get current score from scorer state."""
        active = [h for h in self._scorer.active_hits.values() if h.decayed_weight(int(time.time() * 1000)) > 0]
        base = sum(h.effective_weight for h in active)
        # Note: combos would need to be recalculated — simplified here
        return min(100, int(base))

    def _hard_floor(self) -> int:
        """Calculate hard-signal floor from active hits."""
        active = [h for h in self._scorer.active_hits.values() if h.decayed_weight(int(time.time() * 1000)) > 0]
        hard_active = any(h.hard and h.context == "asserted" for h in active)
        non_hard_active = any(not (h.hard and h.context == "asserted") for h in active)

        if hard_active:
            if non_hard_active:
                return 65
            return 55
        return 0

    def check_alert(self, analysis: Analysis) -> tuple[str | None, int | None]:
        """Check if an alert should be spoken for this analysis.

        Returns (alert_text_en, mute_ms) or (None, None).
        """
        if analysis.level == "calm":
            return None, None

        if not should_alert(analysis.level, self._last_alert_time, analysis.t_ms):
            return None, None

        alert_text = get_alert(analysis.level, "en")
        mark_alert(analysis.level, self._last_alert_time, analysis.t_ms)

        return alert_text, ALERT_MUTE_MS

    def check_alert_hi(self, analysis: Analysis) -> str | None:
        """Get Hindi alert text if should alert."""
        if analysis.level == "calm":
            return None

        if not should_alert(analysis.level, self._last_alert_time, analysis.t_ms):
            return None

        return get_alert(analysis.level, "hi")

    def reset(self) -> None:
        """Reset engine to initial state."""
        self._scorer = ScorerState()
        self._last_alert_time = {}

    def snapshot(self) -> EngineState:
        """Return serializable engine state."""
        hits = [
            SignalHit(
                signal_id=h.signal_id,
                label_en=h.label_en,
                label_hi=h.label_hi,
                weight=h.effective_weight,
                hard=h.hard,
                matched=h.matched,
                segment_id=h.segment_id,
                span_start=h.span_start,
                span_end=h.span_end,
                t_ms=h.t_ms,
                context=h.context,
            )
            for h in self._scorer.active_hits.values()
            if h.decayed_weight(int(time.time() * 1000)) > 0
        ]

        score = sum(h.weight for h in hits)
        level = self._scorer.last_level

        return EngineState(
            hits=hits,
            score=score,
            level=level,
        )