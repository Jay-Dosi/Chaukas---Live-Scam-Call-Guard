"""Health check endpoint — PRD §8.2."""

from fastapi import APIRouter, Depends

from chaukas.config import get_settings
from chaukas.stt.registry import get_stt_provider
from chaukas.tts.sarvam import SarvamTtsProvider
from chaukas.tts.none import NoneTtsProvider

router = APIRouter()


@router.get("/health")
async def health():
    settings = get_settings()
    stt_provider = get_stt_provider()

    # TTS provider
    if settings.resolved_tts_provider().value == "sarvam":
        tts_provider = SarvamTtsProvider(settings.sarvam_api_key)
    else:
        tts_provider = NoneTtsProvider()

    return {
        "stt": {
            "provider": stt_provider.name,
            "streaming": stt_provider.name != "mock",
            "langs": ["hi-IN", "en-IN"],
        },
        "tts": {
            "provider": tts_provider.name,
            "voices": tts_provider.voices,
        },
        "llm": {
            "enabled": settings.resolved_llm_enabled(),
            "model": settings.llm_model if settings.resolved_llm_enabled() else None,
        },
        "ffmpeg": True,  # TODO: check at startup
        "bolna": {
            "configured": bool(settings.bolna_api_key and settings.bolna_agent_id),
            "agent_id": settings.bolna_agent_id[:6] + "..." if settings.bolna_agent_id else None,
        },
        "version": "0.1.0",
    }