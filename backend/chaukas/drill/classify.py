"""Fire-Drill user turn classifier — PRD §7.3.

Deterministic, multilingual, lexicon-based classification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

UserAct = Literal["comply", "question", "verify", "refuse", "hangup", "silence"]
Lang = Literal["hi-IN", "en-IN", "auto"]


@dataclass(frozen=True)
class Classification:
    act: UserAct
    evidence: list[str]
    gave_credential_digits: bool


# Keyword sets for classification
HANGUP_KEYWORDS = {
    "en": ["hang up", "hanging up", "end call", "call you back", "disconnect", "bye"],
    "hi": ["call kat", "phone rakh", "baad mein call", "bye", "disconnect"],
    "hinglish": ["call kat raha", "phone rakh raha", "baad mein call karunga", "bye"],
}

VERIFY_KEYWORDS = {
    "en": ["bank", "branch", "police station", "1930", "call back", "verify", "check with"],
    "hi": ["bank", "branch", "police station", "1930", "wapas call", "check karunga", "pata karunga"],
    "hinglish": ["bank", "branch", "police station", "1930", "call back karunga", "verify karunga", "check karunga", "pata karunga"],
}

REFUSE_KEYWORDS = {
    "en": ["no", "won't", "will not", "refuse", "not sharing", "not telling", "not giving"],
    "hi": ["nahin", "nahi", "nahin dunga", "nahin bataunga", "nahin denge", "nahi dunga"],
    "hinglish": ["nahi", "nahi dunga", "nahi bataunga", "nahi denge", "refuse kar raha"],
}

QUESTION_KEYWORDS = {
    "en": ["who", "what", "why", "which", "where", "how", "?"],
    "hi": ["kaun", "kya", "kyun", "kaun sa", "kahan", "kaise"],
    "hinglish": ["kaun", "kya", "kyun", "kaun sa", "kahan", "kaise", "who", "what", "why"],
}

COMPLY_KEYWORDS = {
    "en": ["yes", "ok", "okay", "sure", "will do", "doing it", "here it is", "telling you"],
    "hi": ["haan", "han", "theek hai", "chalo", "kar deta", "bata deta", "bol deta"],
    "hinglish": ["haan", "han", "ok", "okay", "theek hai", "chalo", "kar deta", "bata deta", "bol deta", "yes", "sure"],
}


def _normalize_lang(lang: str) -> str:
    if lang.startswith("hi"):
        return "hi"
    if lang.startswith("en"):
        return "en"
    return "hinglish"


def _contains_any(text: str, keywords: list[str]) -> list[str]:
    lower = text.lower()
    return [kw for kw in keywords if kw in lower]


def _count_digits(text: str) -> int:
    """Count consecutive digits in text."""
    import re
    matches = re.findall(r'\d+', text)
    if not matches:
        return 0
    return max(len(m) for m in matches)


def classify(text: str, lang: Lang, last_ask: str | None = None) -> Classification:
    """Classify user utterance into a UserAct.

    Rules (PRD §7.3):
    - hangup: button press, or phrases "I'm hanging up", "कॉल काट रहा/रही हूँ", "main phone rakh raha hoon"
    - verify: mentions bank/branch/police station visit or callback, "1930", "I will call back", "मैं खुद पता करूँगा", "मैं बैंक जाकर"
    - refuse: "no", "नहीं दूंगा", "I won't share", "मैं नहीं बताऊंगा"
    - question: question forms "who are you", "आप कौन", "which station", "क्यों", "why"
    - comply: "yes", "haan", "ok ji", "bataiye", "I'll do it", "बता देता हूँ", or >=4 consecutive digits while OTP/PIN was asked
    - silence: no speech/chip within 8s (handled by caller, not here)
    """
    if not text or not text.strip():
        return Classification(act="silence", evidence=[], gave_credential_digits=False)

    nlang = _normalize_lang(lang)
    lower = text.lower()

    # Check hangup
    for kw in HANGUP_KEYWORDS[nlang]:
        if kw in lower:
            return Classification(act="hangup", evidence=[kw], gave_credential_digits=False)

    # Check verify
    for kw in VERIFY_KEYWORDS[nlang]:
        if kw in lower:
            return Classification(act="verify", evidence=[kw], gave_credential_digits=False)

    # Check refuse
    for kw in REFUSE_KEYWORDS[nlang]:
        if kw in lower:
            return Classification(act="refuse", evidence=[kw], gave_credential_digits=False)

    # Check question
    for kw in QUESTION_KEYWORDS[nlang]:
        if kw in lower:
            return Classification(act="question", evidence=[kw], gave_credential_digits=False)

    # Check comply
    for kw in COMPLY_KEYWORDS[nlang]:
        if kw in lower:
            return Classification(act="comply", evidence=[kw], gave_credential_digits=False)

    # Check for credential digits (4+ consecutive digits) when OTP/PIN was asked
    if last_ask in ("otp", "pin", "verification_code", "upi_pin", "aadhaar", "password"):
        digit_count = _count_digits(text)
        if digit_count >= 4:
            return Classification(
                act="comply",
                evidence=[f"{digit_count} digits spoken"],
                gave_credential_digits=True,
            )

    # Default to comply if nothing else matched (user said something)
    return Classification(act="comply", evidence=["unclassified response"], gave_credential_digits=False)