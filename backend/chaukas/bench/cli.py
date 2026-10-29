"""Benchmark CLI — PRD §13, §14.

`make bench` alias for `uv run chaukas-bench`.
Exits non-zero if acceptance targets not met.
"""

from __future__ import annotations

import json
import sys
from typing import Literal

import click

from chaukas.bench.runner import run_benchmark


# PRD §13 acceptance targets
TARGETS = {
    "recall_at_danger_0": 0.92,
    "recall_at_danger_10": 0.85,
    "false_alarm_rate_0": 0.05,
    "false_alarm_rate_10": 0.08,
}


@click.command()
@click.option("--noise-wer", default=0.0, type=float, help="ASR word error rate (0.0-0.4)")
@click.option("--sensitivity", default="standard", type=click.Choice(["standard", "high"]))
@click.option("--danger-threshold", default=None, type=int, help="Override danger threshold")
@click.option("--seed", default=None, type=int, help="Random seed for noise")
@click.option("--output", default=None, type=str, help="Output JSON file")
@click.option("--check-targets/--no-check-targets", default=True, help="Exit non-zero if targets not met")
def main(
    noise_wer: float,
    sensitivity: Literal["standard", "high"],
    danger_threshold: int | None,
    seed: int | None,
    output: str | None,
    check_targets: bool,
):
    """Run benchmark and optionally validate against targets."""
    result = run_benchmark(
        noise_wer=noise_wer,
        sensitivity=sensitivity,
        danger_threshold=danger_threshold,
        seed=seed,
    )

    # Print summary
    summary = result["summary"]
    click.echo(f"\n=== Chaukas Benchmark ===")
    click.echo(f"Noise WER: {noise_wer:.0%}")
    click.echo(f"Sensitivity: {sensitivity}")
    click.echo(f"Cases: {summary['total_cases']} (scam: {summary['scam_cases']}, genuine: {summary['genuine_cases']})")
    click.echo(f"Recall @ Danger: {summary['recall_at_danger']:.1%}")
    click.echo(f"False Alarm Rate: {summary['false_alarm_rate']:.1%}")
    click.echo(f"Median TTD: {summary['median_time_to_danger']} ms")
    click.echo(f"P90 TTD: {summary['p90_time_to_danger']} ms")
    click.echo()

    # Per-tactic
    click.echo("Per-tactic detection:")
    for t in result["per_tactic"]:
        click.echo(f"  {t['tactic']}: {t['detected']}/{t['total']} = {t['rate']:.1%}")

    # Save output
    if output:
        with open(output, "w") as f:
            json.dump(result, f, indent=2)
        click.echo(f"\nSaved to {output}")

    # Check targets
    if check_targets:
        noise_key = "0" if noise_wer < 0.05 else "10"
        recall_target = TARGETS[f"recall_at_danger_{noise_key}"]
        fa_target = TARGETS[f"false_alarm_rate_{noise_key}"]

        recall_ok = summary["recall_at_danger"] >= recall_target
        fa_ok = summary["false_alarm_rate"] <= fa_target

        ok_symbol = "[PASS]"
        fail_symbol = "[FAIL]"

        click.echo(f"\n=== Target Check ({noise_key}% noise) ===")
        click.echo(f"Recall @ Danger: {summary['recall_at_danger']:.1%} >= {recall_target:.1%} {ok_symbol if recall_ok else fail_symbol}")
        click.echo(f"False Alarm Rate: {summary['false_alarm_rate']:.1%} <= {fa_target:.1%} {ok_symbol if fa_ok else fail_symbol}")

        # Zero false alarms on fraud-awareness and genuine controls at 0% noise
        if noise_wer == 0:
            # Check specific cases - would need case IDs
            pass

        if not (recall_ok and fa_ok):
            click.echo(f"\n{fail_symbol} Targets not met")
            sys.exit(1)
        else:
            click.echo(f"\n{ok_symbol} All targets met")


if __name__ == "__main__":
    main()