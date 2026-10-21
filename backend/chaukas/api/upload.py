"""Audio upload endpoint — PRD §8.2.

Decodes with ffmpeg, streams through STT + engine at accelerated pace.
"""

import asyncio
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from chaukas.audio.decode import decode_audio
from chaukas.bench.runner import run_benchmark  # reuse engine

router = APIRouter()


@router.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    """Upload audio file for analysis. Returns job_id."""
    # Validate file
    if file.size and file.size > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 25 MB)")

    allowed_types = {"audio/wav", "audio/mpeg", "audio/mp4", "audio/ogg", "audio/x-m4a"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported audio format")

    # Save to temp file
    suffix = Path(file.filename).suffix if file.filename else ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    # Decode with ffmpeg
    try:
        pcm_path = await decode_audio(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio decode failed: {e}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    # For now, return job_id - actual async processing would be a background task
    import uuid
    job_id = str(uuid.uuid4())

    # TODO: Store job with decoded PCM path for async processing
    # For sync demo, run benchmark directly
    return {"job_id": job_id}