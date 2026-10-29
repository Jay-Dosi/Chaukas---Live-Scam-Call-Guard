"""Sarvam Bulbul TTS adapter — PRD §8.5.

Implemented against Sarvam's current official TTS API docs.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
from pathlib import Path

import httpx

from chaukas.tts.base import TtsProvider
from chaukas.tts.cache import TtsCache

logger = logging.getLogger(__name__)


class SarvamTtsProvider:
    """Sarvam Bulbul TTS provider with disk caching."""

    name = "sarvam"
    voices = ["bulbul:v1"]

    def __init__(self, api_key: str | None = None, cache: TtsCache | None = None):
        self.api_key = api_key or os.environ.get("SARVAM_API_KEY", "")
        self.cache = cache or TtsCache()

    async def synthesize(self, text: str, lang: str, voice: str | None) -> bytes | None:
        if not self.api_key:
            return None

        # Check cache
        cache_key = self._cache_key(text, lang, voice or "bulbul:v1")
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # Sarvam TTS endpoint
        url = "https://api.sarvam.ai/text-to-speech"
        headers = {
            "api-subscription-key": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        target_lang = "hi-IN" if str(lang).startswith("hi") else "en-IN"
        payload = {
            "inputs": [text],
            "target_language_code": target_lang,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code != 200:
                    logger.warning(f"Sarvam TTS failed with {resp.status_code}: {resp.text}")
                    return None

                data = resp.json()
                if "audios" in data and data["audios"]:
                    audio_data = base64.b64decode(data["audios"][0])
                else:
                    return None
        except Exception as e:
            logger.warning(f"Sarvam TTS request exception: {e}")
            return None

        # Cache and return
        self.cache.set(cache_key, audio_data)
        return audio_data

    def _cache_key(self, text: str, lang: str, voice: str) -> str:
        h = hashlib.sha256(f"{text}|{lang}|{voice}".encode()).hexdigest()[:16]
        return f"sarvam_{h}"