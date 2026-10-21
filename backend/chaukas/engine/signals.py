"""Signal definitions, weights, hard flags, and labels for Chaukas detection engine."""

from __future__ import annotations

from typing import NamedTuple


class SignalDef(NamedTuple):
    """A single signal definition."""
    signal_id: str
    label_en: str
    label_hi: str
    weight: float
    hard: bool


# All signals from PRD §6.4 with their weights and hard flags
SIGNALS: dict[str, SignalDef] = {
    "authority_claim": SignalDef(
        signal_id="authority_claim",
        label_en="Authority claim",
        label_hi="अधिकार का दावा",
        weight=12.0,
        hard=False,
    ),
    "digital_arrest": SignalDef(
        signal_id="digital_arrest",
        label_en="Digital arrest threat",
        label_hi="डिजिटल अरेस्ट की धमकी",
        weight=22.0,
        hard=False,
    ),
    "accusation": SignalDef(
        signal_id="accusation",
        label_en="Criminal accusation",
        label_hi="आपराधिक आरोप",
        weight=14.0,
        hard=False,
    ),
    "urgency_threat": SignalDef(
        signal_id="urgency_threat",
        label_en="Urgency or threat",
        label_hi="तुरंत करने या धमकी",
        weight=10.0,
        hard=False,
    ),
    "secrecy_isolation": SignalDef(
        signal_id="secrecy_isolation",
        label_en="Secrecy or isolation demand",
        label_hi="गुप्त रखने या अलग करने की मांग",
        weight=24.0,
        hard=False,
    ),
    "credential_request": SignalDef(
        signal_id="credential_request",
        label_en="Request for credentials",
        label_hi="क्रेडेंशियल्स की मांग",
        weight=30.0,
        hard=True,
    ),
    "transfer_demand": SignalDef(
        signal_id="transfer_demand",
        label_en="Demand to transfer money",
        label_hi="पैसे ट्रांसफर करने की मांग",
        weight=30.0,
        hard=True,
    ),
    "remote_access": SignalDef(
        signal_id="remote_access",
        label_en="Remote access request",
        label_hi="रिमोट एक्सेस की मांग",
        weight=28.0,
        hard=True,
    ),
    "reward_task": SignalDef(
        signal_id="reward_task",
        label_en="Reward or task scam",
        label_hi="इनाम या टास्क स्कैम",
        weight=14.0,
        hard=False,
    ),
    "kyc_expiry": SignalDef(
        signal_id="kyc_expiry",
        label_en="KYC expiry or suspension threat",
        label_hi="केवाईसी समाप्ति या निलंबन की धमकी",
        weight=10.0,
        hard=False,
    ),
    "courier_customs": SignalDef(
        signal_id="courier_customs",
        label_en="Courier or customs issue",
        label_hi="कूरियर या कस्टम समस्या",
        weight=10.0,
        hard=False,
    ),
    "emergency_relative": SignalDef(
        signal_id="emergency_relative",
        label_en="Emergency involving relative",
        label_hi="रिश्तेदार से जुड़ी आपात स्थिति",
        weight=16.0,
        hard=False,
    ),
}

# Combo rules from PRD §6.6
COMBOS: list[tuple[str, tuple[str, ...], float]] = [
    # (combo_id, (signal_a, signal_b_or_more...), bonus)
    ("auth_accusation_arrest", ("authority_claim", "accusation"), 10.0),
    ("auth_digital_arrest", ("authority_claim", "digital_arrest"), 10.0),
    ("auth_urgency", ("authority_claim", "urgency_threat"), 8.0),
    ("accusation_urgency", ("accusation", "urgency_threat"), 8.0),
    ("digital_arrest_urgency", ("digital_arrest", "urgency_threat"), 8.0),
    ("secrecy_hard", ("secrecy_isolation", "credential_request"), 15.0),
    ("secrecy_transfer", ("secrecy_isolation", "transfer_demand"), 15.0),
    ("secrecy_remote", ("secrecy_isolation", "remote_access"), 15.0),
    ("auth_hard_credential", ("authority_claim", "credential_request"), 20.0),
    ("auth_hard_transfer", ("authority_claim", "transfer_demand"), 20.0),
    ("digital_arrest_hard_credential", ("digital_arrest", "credential_request"), 20.0),
    ("digital_arrest_hard_transfer", ("digital_arrest", "transfer_demand"), 20.0),
    ("courier_auth", ("courier_customs", "authority_claim"), 8.0),
    ("courier_accusation", ("courier_customs", "accusation"), 8.0),
    ("reward_transfer", ("reward_task", "transfer_demand"), 12.0),
    ("emergency_transfer", ("emergency_relative", "transfer_demand"), 15.0),
]

# Hard-signal floors from PRD §6.4
HARD_SIGNAL_FLOOR_ALONE = 55
HARD_SIGNAL_FLOOR_WITH_OTHER = 65

# Thresholds from PRD §6.6
THRESHOLD_CAUTION = 30
THRESHOLD_DANGER = 55
THRESHOLD_CRITICAL = 80

# Hysteresis margin
HYSTERESIS_MARGIN = 6

# Decay durations from PRD §6.5
DECAY_DURATION_NON_HARD = 90  # seconds
DECAY_DURATION_HARD = 180  # seconds

# Repetition params from PRD §6.5
REPETITION_ADDITIVE_FACTOR = 0.25  # 25% of weight per repeat
REPETITION_MAX_MULTIPLIER = 2.0  # cap at 2x weight

# Context multipliers from PRD §6.5
CONTEXT_ASSERTED_MULTIPLIER = 1.0
CONTEXT_WARNING_MULTIPLIER = 0.1
CONTEXT_NEGATED_MULTIPLIER = 0.0

# Request verb proximity window from PRD §6.5
REQUEST_VERB_WINDOW = 8

# Warning cue proximity window from PRD §6.5
WARNING_CUE_WINDOW = 7

# Signal weights dict for compatibility with loader.py
SIGNAL_WEIGHTS = {k: v.weight for k, v in SIGNALS.items()}