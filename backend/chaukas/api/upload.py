"""Audio upload endpoint — PRD §8.2.

Decodes with ffmpeg, streams through STT + engine at accelerated pace.
"""

import asyncio
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from chaukas.audio.decode import decode_audio

router = APIRouter()

# In-memory store for upload jobs: job_id -> decoded pcm wav path
UPLOAD_JOBS: dict[str, str] = {}


@router.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    """Upload audio file for analysis. Returns job_id."""
    # Validate file size if available
    if file.size and file.size > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 25 MB)")

    allowed_types = {
        "audio/wav", "audio/wave", "audio/x-wav",
        "audio/mpeg", "audio/mp3",
        "audio/mp4", "audio/ogg", "audio/x-m4a",
        "application/octet-stream",
    }
    if file.content_type and file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported audio format")

    # Save to temp file
    suffix = Path(file.filename).suffix if file.filename else ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    # Decode with ffmpeg (or fallback if already wav)
    pcm_path = None
    try:
        pcm_path = await decode_audio(tmp_path)
    except FileNotFoundError:
        # ffmpeg not installed, if already wav use as-is
        if suffix.lower() in (".wav", ".wave"):
            pcm_path = tmp_path
        else:
            raise HTTPException(status_code=500, detail="ffmpeg binary not found on server to decode non-WAV audio")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio decode failed: {e}")
    finally:
        if pcm_path != tmp_path:
            Path(tmp_path).unlink(missing_ok=True)

    job_id = str(uuid.uuid4())
    UPLOAD_JOBS[job_id] = pcm_path

    return {"job_id": job_id}