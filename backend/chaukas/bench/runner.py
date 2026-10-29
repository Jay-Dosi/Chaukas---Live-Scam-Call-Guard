"""Benchmark runner — PRD §9, §13.

Runs labelled corpus through the engine and computes metrics.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Literal

from chaukas.engine.engine import Engine
from chaukas.engine.scorer import _score_to_level
from chaukas.bench.asr_noise import ASRNoiseConfig, apply_asr_noise_to_segments


CaseLabel = Literal["scam", "genuine"]


def load_corpus() -> list[dict]:
    """Load all corpus cases."""
    corpus_dir = Path(__file__).resolve().parent.parent / "corpus"
    cases = []
    for path in sorted(corpus_dir.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            cases.append(json.load(f))
    return cases


def run_benchmark(
    noise_wer: float = 0.0,
    sensitivity: Literal["standard", "high"] = "standard",
    danger_threshold: int | None = None,
    seed: int | None = None,
) -> dict:
    """Run benchmark on full corpus.

    Returns dict with summary, per_tactic, cases, sweep.
    """
    cases = load_corpus()
    engine = Engine(sensitivity=sensitivity)

    # Override danger threshold if provided
    # (would need engine modification — simplified here)

    results = []
    scam_recall_at_danger = 0
    scam_total = 0
    genuine_false_alarms = 0
    genuine_total = 0
    time_to_danger_values = []

    for case in cases:
        case_id = case["id"]
        label: CaseLabel = case["label"]
        lang = case.get("lang", "en")
        tactics = case.get("tactics", [])
        turns = case["turns"]

        # Apply ASR noise if requested
        if noise_wer > 0:
            noisy_turns = apply_asr_noise_to_segments(turns, ASRNoiseConfig(wer=noise_wer, seed=seed or 42))
        else:
            noisy_turns = turns

        # Run through engine
        engine.reset()
        peak_score = 0
        peak_level = "calm"
        first_danger_turn = None
        first_danger_ms = None
        detected_tactics = set()

        for turn_idx, turn in enumerate(noisy_turns):
            text = turn["text"]
            is_final = True
            t_ms = turn.get("tMs", 0)

            # Create segment
            from chaukas.models.base import Segment, Speaker
            seg = Segment(
                id=f"{case_id}_{turn_idx}",
                text=text,
                is_final=is_final,
                t_start_ms=t_ms,
                t_end_ms=t_ms + 1000,
                lang=lang,
                speaker=Speaker.UNKNOWN,
            )

            analysis = engine.ingest(seg)

            if analysis.score > peak_score:
                peak_score = analysis.score
                peak_level = analysis.level

            if (analysis.level in ("danger", "critical")) and first_danger_turn is None:
                first_danger_turn = turn_idx
                first_danger_ms = t_ms

            for hit in analysis.hits:
                detected_tactics.add(hit.signal_id)

        # Determine result
        passed = False
        if label == "scam":
            scam_total += 1
            # Recall@Danger: reached Danger at or before firstHardAskTurn + 1
            first_hard_ask = case.get("firstHardAskTurn", 999)
            if first_danger_turn is not None and first_danger_turn <= first_hard_ask + 1:
                scam_recall_at_danger += 1
                passed = True
            elif first_danger_turn is not None and "firstHardAskTurn" not in case:
                scam_recall_at_danger += 1
                passed = True
            if first_danger_ms is not None:
                time_to_danger_values.append(first_danger_ms)
        else:
            genuine_total += 1
            # False alarm: ever reached Danger or Critical
            if first_danger_turn is None:
                passed = True
            else:
                genuine_false_alarms += 1

        # Per-tactic recall
        missed = [t for t in tactics if t not in detected_tactics]

        results.append({
            "id": case_id,
            "label": label,
            "lang": lang,
            "tactics": tactics,
            "result": "pass" if passed else "fail",
            "score": peak_score,
            "level": peak_level,
            "time_to_danger": first_danger_ms,
            "explanation": f"Detected: {sorted(detected_tactics)}; Missed: {sorted(missed)}" if missed else f"Detected: {sorted(detected_tactics)}",
            "detected_tactics": list(detected_tactics),
        })

    # Threshold sweep (30 to 90)
    sweep = []
    for threshold in range(30, 91, 5):
        scam_det = sum(1 for r in results if r["label"] == "scam" and r["score"] >= threshold)
        gen_fa = sum(1 for r in results if r["label"] == "genuine" and r["score"] >= threshold)
        sweep.append({
            "threshold": threshold,
            "detection_rate": round(scam_det / scam_total, 4) if scam_total > 0 else 0.0,
            "false_alarm_rate": round(gen_fa / genuine_total, 4) if genuine_total > 0 else 0.0,
        })

    # Per-tactic stats
    tactic_stats = {}
    for case in cases:
        for t in case.get("tactics", []):
            if t not in tactic_stats:
                tactic_stats[t] = {"detected": 0, "total": 0}
            tactic_stats[t]["total"] += 1

    for result in results:
        detected_set = set(result.get("detected_tactics", []))
        for t in result.get("tactics", []):
            if t in detected_set:
                tactic_stats[t]["detected"] += 1

    per_tactic = [
        {"tactic": t, "detected": v["detected"], "total": v["total"], "rate": round(v["detected"] / v["total"], 4) if v["total"] > 0 else 0.0}
        for t, v in sorted(tactic_stats.items())
    ]

    # Summary
    recall = scam_recall_at_danger / scam_total if scam_total > 0 else 0
    fa_rate = genuine_false_alarms / genuine_total if genuine_total > 0 else 0

    time_to_danger_sorted = sorted(time_to_danger_values)
    median_ttd = time_to_danger_sorted[len(time_to_danger_sorted) // 2] if time_to_danger_sorted else 0
    p90_ttd = time_to_danger_sorted[int(len(time_to_danger_sorted) * 0.9)] if time_to_danger_sorted else 0

    return {
        "summary": {
            "recall_at_danger": recall,
            "false_alarm_rate": fa_rate,
            "median_time_to_danger": median_ttd,
            "p90_time_to_danger": p90_ttd,
            "total_cases": len(cases),
            "scam_cases": scam_total,
            "genuine_cases": genuine_total,
        },
        "per_tactic": per_tactic,
        "cases": results,
        "sweep": sweep,
    }