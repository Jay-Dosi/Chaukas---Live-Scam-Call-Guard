"""Fire-Drill state machine — PRD §7.3.

Deterministic state machine with pressure escalation.
Terminal outcomes set by branches, not randomness.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from chaukas.drill.classify import UserAct, classify

UserActType = Literal["comply", "question", "verify", "refuse", "hangup", "silence"]
Outcome = Literal["safe", "unsafe"]


@dataclass(frozen=True)
class CallerNode:
    """A node in the scenario graph."""
    node_id: str
    text: str
    tactics: list[str]
    voice: str
    next: list[dict]  # [{"when": act, "to": node_id}, ...]


@dataclass(frozen=True)
class TerminalNode:
    outcome: Outcome
    debrief_key: str


@dataclass(frozen=True)
class Scenario:
    """Full drill scenario."""
    id: str
    title: dict[str, str]
    lang: str
    label: str  # "scam" | "genuine"
    tactics: list[str]
    expect: dict
    disclosure: dict[str, str]
    start: str
    nodes: dict[str, CallerNode]
    terminals: dict[str, TerminalNode]


@dataclass
class DrillState:
    """Runtime state of a Fire-Drill session."""
    scenario: Scenario
    current_node_id: str
    pressure: int = 0  # 0-5
    turn_count: int = 0
    history: list[dict] = field(default_factory=list)
    scorecard: dict = field(default_factory=dict)
    gave_credential_digits: bool = False
    agreed_to_transfer: bool = False
    stayed_on_isolating_call: bool = False
    ended_call_or_refused_hard: bool = False
    verified_independently: bool = False
    asked_before_complying: bool = False


def load_scenario(scenario_id: str, lang: str) -> Scenario:
    """Load scenario from JSON file."""
    path = Path(__file__).parent.parent / "scenarios" / f"{scenario_id}.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    # Filter to requested language variant
    # Scenario JSON contains all 3 language variants in nodes
    # For simplicity, we assume the caller text is already in the right language
    # The scenario file should have lang-specific nodes or we filter
    return Scenario(**data)


def get_next_node(
    scenario: Scenario,
    current_node_id: str,
    user_act: UserActType,
    pressure: int,
) -> tuple[str, int]:
    """Determine next node and updated pressure based on user action."""
    node = scenario.nodes[current_node_id]

    # Find matching transition
    for transition in node.next:
        if transition["when"] == user_act:
            next_node_id = transition["to"]
            break
    else:
        # Default to first transition if no match
        next_node_id = node.next[0]["to"] if node.next else "END_HANGUP"

    # Update pressure based on user action (PRD §7.3)
    new_pressure = pressure
    if user_act in ("question", "silence", "refuse"):
        new_pressure = min(5, pressure + 1)
    elif user_act == "verify":
        new_pressure = max(0, pressure - 1)
    # comply doesn't change pressure

    return next_node_id, new_pressure


def is_terminal(node_id: str) -> bool:
    return node_id.startswith("END_")


def run_turn(
    state: DrillState,
    user_text: str,
    lang: str,
    user_act: UserActType | None = None,
) -> tuple[DrillState, dict | None]:
    """Process one user turn and return updated state and next caller info (or None if ended)."""
    if user_act is None:
        # Classify from text
        classification = classify(user_text, lang, None)
        user_act = classification.act
        state.gave_credential_digits = classification.gave_credential_digits

    # Update scorecard trackers
    if user_act == "hangup":
        state.ended_call_or_refused_hard = True
    elif user_act == "verify":
        state.verified_independently = True
    elif user_act == "question":
        state.asked_before_complying = True
    elif user_act == "comply" and state.gave_credential_digits:
        # Credential digits already tracked
        pass

    # Record history
    state.history.append({
        "turn": state.turn_count,
        "user_act": user_act,
        "user_text": user_text,
        "node_id": state.current_node_id,
    })

    # Check if current node is terminal
    if is_terminal(state.current_node_id):
        terminal = state.scenario.terminals[state.current_node_id]
        return state, {
            "ended": True,
            "outcome": terminal.outcome,
            "debrief_key": terminal.debrief_key,
        }

    # Get next node
    next_node_id, new_pressure = get_next_node(
        state.scenario,
        state.current_node_id,
        user_act,
        state.pressure,
    )

    state.current_node_id = next_node_id
    state.pressure = new_pressure
    state.turn_count += 1

    # Check if next node is terminal
    if is_terminal(next_node_id):
        terminal = state.scenario.terminals[next_node_id]
        return state, {
            "ended": True,
            "outcome": terminal.outcome,
            "debrief_key": terminal.debrief_key,
        }

    # Return next caller line
    next_node = state.scenario.nodes[next_node_id]
    return state, {
        "ended": False,
        "node_id": next_node_id,
        "text": next_node.text,
        "tactics": next_node.tactics,
        "voice": next_node.voice,
        "pressure": new_pressure,
    }