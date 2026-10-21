"""TTS disk cache with SHA-256 keys."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path


class TtsCache:
    """Disk cache for TTS audio files."""

    def __init__(self, cache_dir: str | Path | None = None):
        self.cache_dir = Path(cache_dir) if cache_dir else Path(".cache/tts")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> bytes | None:
        path = self.cache_dir / f"{key}.wav"
        if path.exists():
            with open(path, "rb") as f:
                return f.read()
        return None

    def set(self, key: str, data: bytes) -> None:
        path = self.cache_dir / f"{key}.wav"
        with open(path, "wb") as f:
            f.write(data)