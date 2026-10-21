"""STT Provider registry — resolves provider based on config."""

from __future__ import annotations

from chaukas.config import get_settings
from chaukas.stt.base import SttProvider
from chaukas.stt.deepgram import DeepgramSttProvider
from chaukas.stt.mock import MockSttProvider
from chaukas.stt.sarvam import SarvamSttProvider


def get_stt_provider() -> SttProvider:
    """Get the configured STT provider based on settings."""
    settings = get_settings()
    resolved = settings.resolved_stt_provider()

    if resolved.value == "sarvam":
        return SarvamSttProvider(settings.sarvam_api_key)
    elif resolved.value == "deepgram":
        return DeepgramSttProvider(settings.deepgram_api_key)
    else:
        return MockSttProvider()