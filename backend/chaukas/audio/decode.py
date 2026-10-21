"""Audio decoding with ffmpeg — PRD §8.2, §8.4.

Uses asyncio.create_subprocess_exec (never shell=True).
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path


async def decode_audio(input_path: str, sample_rate: int = 16000) -> str:
    """Decode audio file to 16kHz mono PCM16 LE.

    Returns path to decoded WAV file.
    """
    output_path = tempfile.mktemp(suffix=".wav")

    proc = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-ar", str(sample_rate),
        "-ac", "1",
        "-f", "wav",
        output_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {stderr.decode()}")

    return output_path


async def stream_pcm(pcm_path: str, chunk_ms: int = 100, speed: float = 1.0):
    """Stream PCM file in chunks at given speed.

    Yields (chunk_bytes, timestamp_ms).
    """
    sample_rate = 16000
    bytes_per_ms = sample_rate * 2 // 1000  # 16-bit mono = 2 bytes/sample
    chunk_bytes = bytes_per_ms * chunk_ms

    with open(pcm_path, "rb") as f:
        # Skip WAV header (44 bytes)
        f.seek(44)
        t_ms = 0
        while True:
            chunk = f.read(chunk_bytes)
            if not chunk:
                break
            yield chunk, t_ms
            t_ms += int(chunk_ms / speed)

            # Pace for real-time or accelerated
            if speed <= 1.0:
                await asyncio.sleep(chunk_ms / 1000.0)
            else:
                await asyncio.sleep(chunk_ms / 1000.0 / speed)