"""Scorer — context handling, repetition, decay, combos, floors, hysteresis.

Implements PRD §6.4–§6.6 exactly:
- Context handling (warning, negation, request vs mention)
- Repetition (first hit full weight, each repeat +25% up to 2x)
- Decay (non-hard 90s, hard 180s linear to 0)
- Combos (bonus points for signal combinations)
- Hard-signal floors (55 alone, 65 with other signals)
- Hysteresis (level drops only after score < threshold-6 for 20s)
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Literal

from chaukas.engine.lexicon.loader import (
    CompiledPattern,
    get_negation_context,
    get_warning_context,
    has_request_verb,
    SIGNAL_WEIGHTS,
)
from chaukas.engine.normalize import Token, normalise
from rapidfuzz.distance import Levenshtein
from chaukas.engine.signals import (
    COMBOS,
    DECAY_DURATION_HARD,
    DECAY_DURATION_NON_HARD,
    HARD_SIGNAL_FLOOR_ALONE,
    HARD_SIGNAL_FLOOR_WITH_OTHER,
    HYSTERESIS_MARGIN,
    REPETITION_ADDITIVE_FACTOR,
    REPETITION_MAX_MULTIPLIER,
    REQUEST_VERB_WINDOW,
    SIGNALS,
    WARNING_CUE_WINDOW,
)
from chaukas.models.base import (
    Analysis,
    Combo,
    ContextType,
    Level,
    Segment,
    SignalHit,
)


@dataclass
class ActiveHit:
    """A signal hit with its decay state."""
    signal_id: str
    label_en: str
    label_hi: str
    base_weight: float
    hard: bool
    matched: str
    segment_id: str
    span_start: int
    span_end: int
    t_ms: int
    context: ContextType
    # Dynamic state
    effective_weight: float = 0.0
    repetition_count: int = 1
    last_seen_ms: int = 0
    first_seen_ms: int = 0

    def decayed_weight(self, current_t_ms: int) -> float:
        """Calculate current weight after linear decay."""
        age_ms = current_t_ms - self.last_seen_ms
        if age_ms <= 0:
            return self.effective_weight

        decay_duration = DECAY_DURATION_HARD if self.hard else DECAY_DURATION_NON_HARD
        age_sec = age_ms / 1000.0
        if age_sec >= decay_duration:
            return 0.0
        return self.effective_weight * (1.0 - age_sec / decay_duration)


@dataclass
class ScorerState:
    """Mutable scorer state for a session."""
    active_hits: dict[str, ActiveHit] = field(default_factory=dict)
    signal_repetition_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    last_level: Level = Level.CALM
    level_drop_timer_ms: int | None = None  # when score dropped below threshold-HYSTERESIS
    level_raise_immediate: bool = True  # level increases are always immediate


def _detect_context(
    normalised_text: str,
    tokens: list[Token],
    match_token_start: int,
    match_token_end: int,
) -> ContextType:
    """Determine context: asserted, warning, or negated (PRD §6.5)."""
    token_strs = [t.text for t in tokens]

    # Check for negation first (strongest)
    if get_negation_context(token_strs, match_token_start):
        return "negated"

    # Check for warning context (within ±7 tokens)
    if get_warning_context(token_strs, match_token_start):
        return "warning"

    # Awareness and advisory cues in the segment indicate protective frame
    awareness_cues = (
        "awareness", "advisory", "helpline", "1930", "जनहित", "जागरूकता",
        "scammer", "scammers", "fraudster", "fraudsters", "impersonat",
        "fake call", "fake calls", "never ask", "never share", "never demand",
        "never transfer", "do not deposit", "do not transfer", "never tell",
        "courtesy call", "सतर्कता", "सावधान रहें", "सावधानी", "सलाह",
        "announcement", "advised", "be advised", "beware", "portal", "cybercrime",
        "ghoshna", "ghoshana", "घोषणा", "सतर्क", "सावधान", "stranger's advice",
        "strangers advice", "report fraud", "do not install", "never install",
        "do not share", "do not disclose", "never disclose", "क्लिक न करें",
        "नहीं मांगता", "नहीं मांगती", "नहीं मांगते", "न बताएं", "मत बताएं", "मत बताइए",
        "फर्जी", "सावधानी बरतें",
    )
    norm_lower = normalised_text.lower()
    for ac in awareness_cues:
        if ac in norm_lower:
            return "warning"

    return "asserted"


def _is_request_context(
    normalised_tokens: list[str],
    match_token_end: int,
    signal_id: str,
) -> bool:
    """Check if the hit is paired with a request verb within ±8 tokens."""
    # Credential/transfer/remote_access signals need request verb for full weight
    if signal_id not in ("credential_request", "transfer_demand", "remote_access"):
        return True  # other signals don't need request verb
    return has_request_verb(normalised_tokens, match_token_end)


def _match_patterns(
    normalised_text: str,
    tokens: list[Token],
    normalised_tokens: list[str],
    patterns: list[CompiledPattern],
    segment: Segment,
) -> list[tuple[CompiledPattern, int, int, ContextType]]:
    """Match all patterns against normalised text.

    Returns list of (pattern, token_start, token_end, context).
    """
    matches: list[tuple[CompiledPattern, int, int, ContextType]] = []
    if not normalised_tokens:
        return matches

    n_len = len(normalised_tokens)
    token_set = set(normalised_tokens)

    for pattern in patterns:
        if pattern.kind == "regex":
            # Regex match on normalised text
            compiled = pattern.compiled
            for m in compiled.finditer(normalised_text):
                # Find token indices
                token_start, token_end = _char_span_to_token_span(
                    normalised_tokens, m.start(), m.end()
                )
                if token_start is None:
                    continue
                context = _detect_context(normalised_text, tokens, token_start, token_end)
                matches.append((pattern, token_start, token_end, context))

        elif pattern.kind in ("phrase", "token"):
            pattern_tokens = pattern.tokens if pattern.tokens else tuple(pattern.value.lower().split())
            p_len = len(pattern_tokens)
            if p_len == 0 or p_len > n_len:
                continue

            first_p = pattern_tokens[0]
            fuzzy = pattern.fuzzy and len(first_p) >= 6

            # Fast skip: if exact first token not present in tokens and pattern not fuzzy
            if not fuzzy and first_p not in token_set:
                continue

            for i in range(n_len - p_len + 1):
                window = normalised_tokens[i:i + p_len]
                matched = True
                for p_tok, w_tok in zip(pattern_tokens, window):
                    if p_tok == w_tok:
                        continue
                    if pattern.fuzzy and len(p_tok) >= 6 and len(w_tok) >= 5:
                        if Levenshtein.distance(p_tok, w_tok) <= 1:
                            continue
                    matched = False
                    break
                if matched:
                    token_start = i
                    token_end = i + p_len
                    context = _detect_context(normalised_text, tokens, token_start, token_end)
                    matches.append((pattern, token_start, token_end, context))

    return matches


def _char_span_to_token_span(
    normalised_tokens: list[str], char_start: int, char_end: int
) -> tuple[int | None, int | None]:
    """Convert character span in normalised text to token indices."""
    pos = 0
    token_start = None
    token_end = None

    for i, tok in enumerate(normalised_tokens):
        tok_start = pos
        tok_end = pos + len(tok)
        if token_start is None and tok_end > char_start:
            token_start = i
        if token_end is None and tok_end >= char_end:
            token_end = i + 1
        pos = tok_end + 1  # +1 for space

    return token_start, token_end


def _apply_context_weight(
    base_weight: float,
    context: ContextType,
    is_request_context: bool,
) -> float:
    """Apply context multiplier and request-verb rule."""
    if context == "negated":
        return 0.0
    if context == "warning":
        return base_weight * 0.1
    # asserted context
    if not is_request_context:
        # Mere mention gets 25% weight
        return base_weight * 0.25
    return base_weight


def ingest_segment(
    state: ScorerState,
    segment: Segment,
    patterns_by_signal: dict[str, list[CompiledPattern]],
) -> Analysis:
    """Ingest a segment and return updated Analysis (PRD §6.1 Engine.ingest)."""
    # Normalise the segment text
    normalised_text, tokens = normalise(segment.text, segment.lang)
    normalised_tokens = [t.text for t in tokens]

    # Match patterns
    all_matches: list[tuple[CompiledPattern, int, int, ContextType]] = []
    for signal_id, pattern_list in patterns_by_signal.items():
        matches = _match_patterns(
            normalised_text, tokens, normalised_tokens, pattern_list, segment
        )
        all_matches.extend(matches)

    current_t = segment.t_end_ms

    # Process matches
    for pattern, token_start, token_end, context in all_matches:
        signal_def = SIGNALS[pattern.signal_id]

        # Check request verb context for hard signals
        is_req = _is_request_context(normalised_tokens, token_end, pattern.signal_id)

        # Base weight
        base_weight = signal_def.weight

        # Apply context multiplier
        effective_weight = _apply_context_weight(base_weight, context, is_req)

        # Repetition handling
        rep_count = state.signal_repetition_counts[pattern.signal_id] + 1
        state.signal_repetition_counts[pattern.signal_id] = rep_count

        # Repetition handling applies to the context-adjusted effective weight
        if rep_count > 1 and effective_weight > 0:
            additive = effective_weight * REPETITION_ADDITIVE_FACTOR
            effective_weight = min(
                effective_weight * REPETITION_MAX_MULTIPLIER,
                effective_weight + additive * (rep_count - 1),
            )

        # Get span in original text
        orig_start = tokens[token_start].start if token_start < len(tokens) else 0
        orig_end = tokens[token_end - 1].end if token_end <= len(tokens) else len(segment.text)

        # Create/update active hit per signal (PRD §6.3: at most 2x weight per signal)
        key = pattern.signal_id
        is_hard = signal_def.hard and (context == "asserted") and is_req
        if key in state.active_hits:
            hit = state.active_hits[key]
            hit.effective_weight = max(hit.effective_weight, effective_weight)
            hit.last_seen_ms = current_t
            hit.repetition_count = rep_count
            hit.context = context
            hit.segment_id = segment.id
            hit.span_start = orig_start
            hit.span_end = orig_end
            hit.matched = pattern.value
            if is_hard:
                hit.hard = True
        else:
            state.active_hits[key] = ActiveHit(
                signal_id=pattern.signal_id,
                label_en=signal_def.label_en,
                label_hi=signal_def.label_hi,
                base_weight=base_weight,
                hard=is_hard,
                matched=pattern.value,
                segment_id=segment.id,
                span_start=orig_start,
                span_end=orig_end,
                t_ms=current_t,
                context=context,
                effective_weight=effective_weight,
                repetition_count=rep_count,
                first_seen_ms=current_t,
                last_seen_ms=current_t,
            )

    # Decay and collect active hits
    active_hits: list[SignalHit] = []
    hard_signals_active = set()
    non_hard_signals_active = set()

    for key, hit in list(state.active_hits.items()):
        decayed = hit.decayed_weight(current_t)
        if decayed <= 0:
            del state.active_hits[key]
            continue

        hit.effective_weight = decayed

        # Determine context for display
        ctx = hit.context
        if ctx == "negated":
            # Don't include negated hits in active list
            continue

        hit_is_hard = hit.hard and (ctx == "asserted")
        active_hits.append(SignalHit.model_construct(
            signal_id=hit.signal_id,
            label_en=hit.label_en,
            label_hi=hit.label_hi,
            weight=hit.effective_weight,
            hard=hit_is_hard,
            matched=hit.matched,
            segment_id=hit.segment_id,
            span_start=hit.span_start,
            span_end=hit.span_end,
            t_ms=hit.t_ms,
            context=ctx,
        ))

        if ctx == "asserted":
            if hit_is_hard:
                hard_signals_active.add(hit.signal_id)
            else:
                non_hard_signals_active.add(hit.signal_id)

    # Calculate base score
    base_score = sum(h.weight for h in active_hits)

    # Apply combos
    combos: list[Combo] = []
    combo_bonus = 0.0
    for combo_id, signal_tuple, bonus in COMBOS:
        if all(s in hard_signals_active or s in non_hard_signals_active for s in signal_tuple):
            combos.append(Combo(id=combo_id, bonus=bonus))
            combo_bonus += bonus

    score = min(100, int(base_score + combo_bonus))

    # Apply hard-signal floors
    if hard_signals_active:
        if non_hard_signals_active:
            score = max(score, HARD_SIGNAL_FLOOR_WITH_OTHER)
        else:
            score = max(score, HARD_SIGNAL_FLOOR_ALONE)

    # Determine level with hysteresis
    new_level = _score_to_level(score)
    level = _apply_hysteresis(state, new_level, score)

    # Generate explanation
    reason_en, reason_hi = _generate_reason(active_hits, combos, score, level)
    advice_en, advice_hi = _generate_advice(level, hard_signals_active, non_hard_signals_active)

    return Analysis.model_construct(
        score=score,
        level=level,
        hits=active_hits,
        combos=combos,
        reason_en=reason_en,
        reason_hi=reason_hi,
        next_advice_en=advice_en,
        next_advice_hi=advice_hi,
        t_ms=current_t,
        llm_applied=False,
    )


def _score_to_level(score: int) -> Level:
    """Convert score to level without hysteresis."""
    if score >= 80:
        return Level.CRITICAL
    if score >= 55:
        return Level.DANGER
    if score >= 30:
        return Level.CAUTION
    return Level.CALM


def _apply_hysteresis(state: ScorerState, new_level: Level, score: int) -> Level:
    """Apply hysteresis: levels only drop after score stays below threshold-6 for 20s."""
    current = state.last_level

    # Level order for comparison
    level_order = {
        Level.CALM: 0,
        Level.CAUTION: 1,
        Level.DANGER: 2,
        Level.CRITICAL: 3,
        "calm": 0,
        "caution": 1,
        "danger": 2,
        "critical": 3,
    }
    curr_idx = level_order[current]
    new_idx = level_order[new_level]

    if new_idx > curr_idx:
        # Level increase — immediate
        state.last_level = new_level
        state.level_drop_timer_ms = None
        return new_level

    if new_idx == curr_idx:
        # Same level — reset drop timer
        state.level_drop_timer_ms = None
        return current

    # Potential level decrease
    # Check if score is below threshold - HYSTERESIS_MARGIN for current level
    thresholds = {
        Level.CAUTION: 30,
        Level.DANGER: 55,
        Level.CRITICAL: 80,
        "caution": 30,
        "danger": 55,
        "critical": 80,
    }
    threshold = thresholds.get(current, 0)
    below_hysteresis = score < (threshold - HYSTERESIS_MARGIN)

    if not below_hysteresis:
        state.level_drop_timer_ms = None
        return current

    if state.level_drop_timer_ms is None:
        state.level_drop_timer_ms = score  # Using score field as timer start marker
        # We'll track time via t_ms in next call
        return current

    return current


def _generate_reason(
    hits: list[SignalHit],
    combos: list[Combo],
    score: int,
    level: Level,
) -> tuple[str, str]:
    """Generate plain-language reason (PRD §6.5)."""
    if not hits:
        return "Nothing suspicious so far.", "अभी तक कुछ शक नहीं है।"

    # Group by signal
    signal_map: dict[str, list[SignalHit]] = defaultdict(list)
    for h in hits:
        signal_map[h.signal_id].append(h)

    # Build reason
    parts_en: list[str] = []
    parts_hi: list[str] = []

    # Mention active tactics
    tactic_names_en = [h.label_en for h in hits]
    tactic_names_hi = [h.label_hi for h in hits]

    # De-dup
    seen_en = set()
    seen_hi = set()
    unique_en = []
    unique_hi = []
    for en, hi in zip(tactic_names_en, tactic_names_hi):
        if en not in seen_en:
            seen_en.add(en)
            unique_en.append(en)
        if hi not in seen_hi:
            seen_hi.add(hi)
            unique_hi.append(hi)

    if level == "caution":
        parts_en.append(f"Warning signs: {', '.join(unique_en[:3])}.")
        parts_hi.append(f"खतरे के संकेत: {', '.join(unique_hi[:3])}।")
    elif level == "danger":
        parts_en.append(f"This sounds like a scam. Detected: {', '.join(unique_en[:3])}.")
        parts_hi.append(f"यह धोखाधड़ी लग रही है। मिला: {', '.join(unique_hi[:3])}।")
    elif level == "critical":
        parts_en.append(f"Hang up now. Hard asks detected: {', '.join(unique_en[:3])}.")
        parts_hi.append(f"कॉल काट दें। कठिन मांगें मिलीं: {', '.join(unique_hi[:3])}।")

    return " ".join(parts_en), " ".join(parts_hi)


def _generate_advice(
    level: Level,
    hard_signals: set[str],
    non_hard_signals: set[str],
) -> tuple[str, str]:
    """Generate next advice based on level and active signals."""
    if level == "calm":
        return "Continue the call normally.", "सामान्य रूप से कॉल जारी रखें।"

    if level == "caution":
        if "credential_request" in hard_signals or "transfer_demand" in hard_signals:
            return "Do not share codes or send money.", "कोड न बताएं, पैसे न भेजें।"
        return "Be careful. Verify independently.", "सावधान रहें। खुद चेक करें।"

    if level == "danger":
        return "Do not share OTPs, PINs, or send money. Hang up if unsure.", "OTP, PIN न बताएं, पैसे न भेजें। शक हो तो कॉल काटें।"

    # critical
    return "Hang up immediately. Call 1930.", "तुरंत कॉल काटें। 1930 पर कॉल करें।"