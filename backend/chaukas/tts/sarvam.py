"""Sarvam Bulbul TTS adapter — PRD §8.5.

Implemented against Sarvam's current official TTS API docs.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import httpx

from chaukas.tts.base import TtsProvider
from chaukas.tts.cache import TtsCache


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
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "text": text,
            "language_code": lang,
            "voice": voice or "bulbul:v1",
            "sample_rate": 16000,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                return None

            audio_data = resp.content

        # Cache and return
        self.cache.set(cache_key, audio_data)
        return audio_data

    def _cache_key(self, text: str, lang: str, voice: str) -> str:
        h = hashlib.sha256(f"{text}|{lang}|{voice}".encode()).hexdigest()[:16]
        return f"sarvam_{h}"