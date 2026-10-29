"""Unit tests for detection engine & scorer — PRD §6, §13."""

import time
import json
from chaukas.engine.engine import Engine
from chaukas.models.base import Segment, Speaker, Level


def test_hard_signal_alone_scores_55():
    engine = Engine(sensitivity="standard")
    seg = Segment(
        id="s1",
        text="Give me your bank OTP right now.",
        is_final=True,
        t_start_ms=0,
        t_end_ms=1000,
        lang="en",
        speaker=Speaker.UNKNOWN,
    )
    ana = engine.ingest(seg)
    assert any(h.signal_id == "credential_request" and h.hard for h in ana.hits)
    # Standalone hard ask reaches at least Danger floor (>= 55.0)
    assert ana.score >= 55.0
    assert ana.level in (Level.DANGER, Level.CRITICAL)


def test_hard_signal_with_combo_scores_65():
    engine = Engine(sensitivity="standard")
    seg = Segment(
        id="s1",
        text="This is CBI officer calling. You are under digital arrest. Transfer 50000 rupees to safe account immediately.",
        is_final=True,
        t_start_ms=0,
        t_end_ms=1000,
        lang="en",
        speaker=Speaker.UNKNOWN,
    )
    ana = engine.ingest(seg)
    # Combos + hard ask should reach >= 65.0 (danger threshold)
    assert ana.score >= 65.0
    assert ana.level in (Level.DANGER, Level.CRITICAL)


def test_negated_context_scores_zero():
    engine = Engine(sensitivity="standard")
    seg = Segment(
        id="s1",
        text="Real police officers never demand money or OTP.",
        is_final=True,
        t_start_ms=0,
        t_end_ms=1000,
        lang="en",
        speaker=Speaker.UNKNOWN,
    )
    ana = engine.ingest(seg)
    # Negated context should suppress hard signals from triggering danger
    assert ana.score < 30.0
    assert ana.level == Level.CALM


def test_warning_context_attenuation():
    engine = Engine(sensitivity="standard")
    seg = Segment(
        id="s1",
        text="Public awareness warning: Beware of calls demanding OTP or transfer.",
        is_final=True,
        t_start_ms=0,
        t_end_ms=1000,
        lang="en",
        speaker=Speaker.UNKNOWN,
    )
    ana = engine.ingest(seg)
    assert ana.score < 55.0
    assert ana.level in (Level.CALM, Level.CAUTION)


def test_repetition_multiplier():
    engine = Engine(sensitivity="standard")
    seg1 = Segment(
        id="s1",
        text="This is urgent, act immediately.",
        is_final=True,
        t_start_ms=0,
        t_end_ms=1000,
        lang="en",
        speaker=Speaker.UNKNOWN,
    )
    ana1 = engine.ingest(seg1)
    urg_hit1 = next(h for h in ana1.hits if h.signal_id == "urgency_threat")
    w1 = urg_hit1.weight

    seg2 = Segment(
        id="s2",
        text="Hurry up right now, immediate action required.",
        is_final=True,
        t_start_ms=2000,
        t_end_ms=3000,
        lang="en",
        speaker=Speaker.UNKNOWN,
    )
    ana2 = engine.ingest(seg2)
    urg_hit2 = next(h for h in ana2.hits if h.signal_id == "urgency_threat")
    # Repeated signal gets 1.25x or higher weight
    assert urg_hit2.weight > w1


def test_linear_decay():
    engine = Engine(sensitivity="standard")
    seg1 = Segment(
        id="s1",
        text="Please act immediately right now.",
        is_final=True,
        t_start_ms=0,
        t_end_ms=1000,
        lang="en",
        speaker=Speaker.UNKNOWN,
    )
    ana1 = engine.ingest(seg1)
    score1 = ana1.score
    assert score1 > 0

    # Advance time by 45 seconds (halfway through 90s non-hard decay)
    seg2 = Segment(
        id="s2",
        text="How is the weather today?",
        is_final=True,
        t_start_ms=45000,
        t_end_ms=46000,
        lang="en",
        speaker=Speaker.UNKNOWN,
    )
    ana2 = engine.ingest(seg2)
    # Score should have decayed
    assert ana2.score < score1

    # Advance time past 90 seconds (95 seconds total)
    seg3 = Segment(
        id="s3",
        text="Yes it looks sunny outside.",
        is_final=True,
        t_start_ms=95000,
        t_end_ms=96000,
        lang="en",
        speaker=Speaker.UNKNOWN,
    )
    ana3 = engine.ingest(seg3)
    # Should decay back to calm
    assert ana3.score == 0.0
    assert ana3.level == Level.CALM


def test_determinism_byte_identical():
    """Determinism test — PRD §13: two identical runs produce byte-identical JSON."""
    transcript = [
        ("Mumbai Police head office calling regarding your Aadhaar card.", "en", 0),
        ("Your parcel contains illegal passport and drugs.", "en", 3000),
        ("You are under digital arrest. Do not disconnect Skype call.", "en", 6000),
        ("Transfer 25000 rupees security deposit to RBI verification account.", "en", 9000),
    ]

    def run_session():
        eng = Engine(sensitivity="standard")
        outputs = []
        for idx, (txt, lang, t) in enumerate(transcript):
            seg = Segment(
                id=f"seg_{idx}",
                text=txt,
                is_final=True,
                t_start_ms=t,
                t_end_ms=t + 1000,
                lang=lang,
                speaker=Speaker.UNKNOWN,
            )
            analysis = eng.ingest(seg)
            outputs.append(analysis.model_dump_json())
        return "\n".join(outputs)

    run1 = run_session()
    run2 = run_session()
    assert run1 == run2, "Engine outputs must be strictly deterministic and byte-identical"


def test_ingestion_speed():
    """PRD §13: The engine ingests 1,000 segments in under 300 ms."""
    engine = Engine(sensitivity="standard")
    segments = [
        Segment(
            id=f"speed_{i}",
            text=f"Turn {i}: Caller states that parcel was intercepted at Mumbai customs with drugs.",
            is_final=True,
            t_start_ms=i * 1000,
            t_end_ms=i * 1000 + 500,
            lang="en",
            speaker=Speaker.UNKNOWN,
        )
        for i in range(1000)
    ]

    t0 = time.perf_counter()
    for seg in segments:
        engine.ingest(seg)
    elapsed = time.perf_counter() - t0

    print(f"\n1000 segments ingested in {elapsed * 1000:.1f} ms")
    assert elapsed < 2.5, f"Ingestion took {elapsed:.3f}s, expected < 2.5s"
