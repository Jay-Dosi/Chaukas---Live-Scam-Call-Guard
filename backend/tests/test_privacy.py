"""Privacy test — PRD §13: No transcript text or audio appears in logs at info level."""

import logging
from chaukas.engine.engine import Engine
from chaukas.models.base import Segment, Speaker


def test_no_transcript_in_info_logs(caplog):
    caplog.set_level(logging.INFO)

    secret_text = "SENSITIVE_AADHAAR_9999_8888_SECRET_OTP"
    engine = Engine(sensitivity="standard")
    seg = Segment(
        id="priv_1",
        text=secret_text,
        is_final=True,
        t_start_ms=0,
        t_end_ms=1000,
        lang="en",
        speaker=Speaker.UNKNOWN,
    )
    engine.ingest(seg)

    # Check all records emitted at INFO level
    for record in caplog.records:
        if record.levelno == logging.INFO:
            assert secret_text not in record.getMessage(), (
                f"Transcript text leaked into INFO log: {record.getMessage()}"
            )

