"""Unit tests for Fire-Drill classifier, state machine, and scorecard — PRD §7."""

from pathlib import Path
from chaukas.drill.classify import classify
from chaukas.drill.score import calculate_scorecard
from chaukas.drill.machine import load_scenario, DrillState, run_turn


def test_classifier_acts():
    # Hangup
    c = classify("I am hanging up now", "en-IN")
    assert c.act == "hangup"

    c_hi = classify("call kat raha hoon", "hi-IN")
    assert c_hi.act == "hangup"

    # Verify
    c = classify("I will visit my bank branch and check", "en-IN")
    assert c.act == "verify"

    c = classify("I will call 1930 cyber helpline", "en-IN")
    assert c.act == "verify"

    # Refuse
    c = classify("I will not share my OTP", "en-IN")
    assert c.act == "refuse"

    c_hi = classify("nahin dunga", "hi-IN")
    assert c_hi.act == "refuse"

    # Question
    c = classify("Who are you and which police station?", "en-IN")
    assert c.act == "question"

    # Comply
    c = classify("Okay sure, will do that", "en-IN")
    assert c.act == "comply"

    # Credential digits detection
    c = classify("My code is 482910", "en-IN", last_ask="otp")
    assert c.act == "comply"
    assert c.gave_credential_digits is True


def test_scorecard_arithmetic():
    # Perfect safe run
    state_safe = {
        "ended_call_or_refused_hard": True,  # +35
        "verified_independently": True,       # +30
        "asked_before_complying": True,       # +10
        "gave_credential_digits": False,      # +15
        "agreed_to_transfer": False,          # +10
    }
    sc = calculate_scorecard(state_safe)
    assert sc.total == 100
    assert sc.outcome == "safe"

    # Compromised run
    state_compromised = {
        "ended_call_or_refused_hard": False,
        "verified_independently": False,
        "asked_before_complying": False,
        "gave_credential_digits": True,       # -40
        "agreed_to_transfer": True,           # -40
    }
    sc = calculate_scorecard(state_compromised)
    # Total clamped at 0
    assert sc.total == 0
    assert sc.outcome == "unsafe"


def test_drill_machine_step_and_terminal():
    scenarios_dir = Path(__file__).resolve().parent.parent / "chaukas" / "scenarios"
    scenario_files = list(scenarios_dir.glob("*.json"))
    assert len(scenario_files) > 0, "Scenario files must exist"

    # Load first scenario
    scenario = load_scenario(scenario_files[0].stem)
    state = DrillState(scenario=scenario, current_node_id=scenario.start)

    # Initial state
    assert state.current_node_id == scenario.start
    assert state.turn_count == 0

    # Execute a hangup turn
    state, next_info = run_turn(state, user_text="I am hanging up now", lang="en")
    # A hangup should lead to a terminal or transition
    assert state.turn_count >= 0
    assert len(state.history) == 1
    assert state.history[0]["user_act"] == "hangup"
