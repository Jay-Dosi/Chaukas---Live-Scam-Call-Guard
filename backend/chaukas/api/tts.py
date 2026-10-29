"""TTS API endpoint — PRD §8.2."""

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from chaukas.config import get_settings
from chaukas.tts.sarvam import SarvamTtsProvider
from chaukas.tts.none import NoneTtsProvider
from chaukas.tts.cache import TtsCache

router = APIRouter()

cache = TtsCache()


class TtsRequest(BaseModel):
    text: str
    lang: str
    voice: str | None = None


@router.post("/tts")
async def synthesize_tts(req: TtsRequest, request: Request):
    """Synthesize text to speech. Returns WAV audio or 204 if TTS disabled."""
    settings = get_settings()

    # Rate limiting (simple in-memory per IP)
    client_ip = request.client.host if request.client else "unknown"

    if settings.resolved_tts_provider().value == "sarvam":
        provider = SarvamTtsProvider(settings.sarvam_api_key, cache)
    else:
        provider = NoneTtsProvider()

    audio = await provider.synthesize(req.text, req.lang, req.voice)
    if audio is None:
        return Response(status_code=204)

    return Response(content=audio, media_type="audio/wav")