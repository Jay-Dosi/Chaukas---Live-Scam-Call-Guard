"""Alert copy for Chaukas — PRD §6.7.

Short, calm, imperative, in the user's language.
Spoken text <= 18 words.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from chaukas.models.base import Level


@dataclass(frozen=True)
class AlertText:
    en: str
    hi: str


# PRD §6.7 table
ALERTS: dict[Level, AlertText] = {
    "calm": AlertText(
        en="Nothing suspicious so far.",
        hi="अभी तक कुछ शक नहीं है।",
    ),
    "caution": AlertText(
        en="Be careful. This call has some warning signs.",
        hi="सावधान रहें। इस कॉल में कुछ खतरे के संकेत हैं।",
    ),
    "danger": AlertText(
        en="Warning. This sounds like a scam. Do not share any code or send money.",
        hi="चेतावनी। यह धोखाधड़ी लग रही है। कोई कोड न बताएं, पैसे न भेजें।",
    ),
    "critical": AlertText(
        en="Hang up now. No real officer asks for money or codes. Call one nine three zero.",
        hi="कॉल काट दें। कोई असली अधिकारी पैसे या कोड नहीं मांगता। एक नौ तीन शून्य पर कॉल करें।",
    ),
}

# Cooldown in milliseconds per PRD F-LG-6
ALERT_COOLDOWN_MS = 25_000

# Mute duration for transcript ingestion during alert playback
ALERT_MUTE_MS = 300


def get_alert(level: Level, lang: Literal["en", "hi"] = "en") -> str:
    """Get alert text for a level in the specified language."""
    alert = ALERTS.get(level)
    if not alert:
        return ""
    return alert.hi if lang == "hi" else alert.en


def should_alert(level: Level, last_alert_time: dict[Level, int], current_time_ms: int) -> bool:
    """Check if we should speak an alert for this level (cooldown enforcement)."""
    if level == "calm":
        return False

    last = last_alert_time.get(level, 0)
    return (current_time_ms - last) >= ALERT_COOLDOWN_MS


def mark_alert(level: Level, last_alert_time: dict[Level, int], current_time_ms: int) -> None:
    """Record that an alert was spoken for this level."""
    if level != "calm":
        last_alert_time[level] = current_time_ms