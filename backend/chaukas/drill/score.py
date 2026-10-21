"""Fire-Drill scorecard — PRD §7.4.

Out of 100, computed from observable behaviours.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Outcome = Literal["safe", "unsafe"]


@dataclass(frozen=True)
class ScorecardItem:
    label: str
    points: int


@dataclass(frozen=True)
class ScorecardResult:
    total: int
    items: list[ScorecardItem]
    outcome: Outcome


def calculate_scorecard(state: dict) -> ScorecardResult:
    """Calculate scorecard from final drill state.

    Behaviours and points from PRD §7.4:

    | Behaviour | Points |
    |---|---|
    | Ended the call or refused a hard ask | +35 |
    | Verified independently (bank, 1930, family) | +30 |
    | Asked who/why before complying | +10 |
    | Did not disclose any credential digits | +15 |
    | Did not agree to transfer | +10 |
    | Agreed to transfer | −40 |
    | Spoke credential digits | −40 |
    | Stayed on isolating video call after secrecy demand, for more than 3 turns | −10 |
    | Genuine-call control: did not end a genuine call as a scam | +100 baseline; −50 if user called it a scam and hung up on a genuine bank call without verifying |

    Clamp 0–100.
    """
    items: list[ScorecardItem] = []
    total = 0

    # Positive behaviours
    if state.get("ended_call_or_refused_hard"):
        items.append(ScorecardItem("Ended call or refused hard ask", 35))
        total += 35

    if state.get("verified_independently"):
        items.append(ScorecardItem("Verified independently", 30))
        total += 30

    if state.get("asked_before_complying"):
        items.append(ScorecardItem("Asked who/why before complying", 10))
        total += 10

    if not state.get("gave_credential_digits"):
        items.append(ScorecardItem("Did not disclose credential digits", 15))
        total += 15

    if not state.get("agreed_to_transfer"):
        items.append(ScorecardItem("Did not agree to transfer", 10))
        total += 10

    # Negative behaviours
    if state.get("agreed_to_transfer"):
        items.append(ScorecardItem("Agreed to transfer", -40))
        total -= 40

    if state.get("gave_credential_digits"):
        items.append(ScorecardItem("Spoke credential digits", -40))
        total -= 40

    if state.get("stayed_on_isolating_call", 0) > 3:
        items.append(ScorecardItem("Stayed on isolating video call > 3 turns", -10))
        total -= 10

    # Genuine call control
    if state.get("genuine_call"):
        if state.get("hung_up_on_genuine_without_verifying"):
            items.append(ScorecardItem("Hung up on genuine call without verifying", -50))
            total -= 50
        else:
            items.append(ScorecardItem("Correctly handled genuine call", 100))
            total += 100

    # Clamp 0-100
    total = max(0, min(100, total))

    # Determine outcome
    outcome: Outcome = "safe" if total >= 50 else "unsafe"

    return ScorecardResult(total=total, items=items, outcome=outcome)