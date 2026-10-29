"""Unit tests for WebSocket endpoints — PRD §8, §13."""

import json
from fastapi.testclient import TestClient
from chaukas.main import app

client = TestClient(app)


def test_ws_session_live_mode():
    with client.websocket_connect("/ws/session") as ws:
        # Send start message
        ws.send_json({
            "type": "start",
            "mode": "live",
            "lang": "en-IN",
            "sensitivity": "standard",
        })

        ready = ws.receive_json()
        assert ready["type"] == "ready"
        assert "providers" in ready

        # Send a text message (client transcription fallback)
        ws.send_json({
            "type": "text",
            "id": "s_1",
            "text": "Hello, this is officer Sharma calling from Delhi Police.",
            "is_final": True,
            "t_ms": 1000,
        })

        # Expect an analysis event (or wait past any initial partials)
        found_analysis = False
        for _ in range(10):
            msg = ws.receive_json()
            if msg.get("type") == "analysis":
                found_analysis = True
                assert "score" in msg["analysis"]
                assert "level" in msg["analysis"]
                break
        assert found_analysis


def test_ws_session_inject_mode():
    with client.websocket_connect("/ws/session") as ws:
        # Send start message with inject mode
        ws.send_json({
            "type": "start",
            "mode": "inject",
            "scenario_id": "courier-customs-en-01",
            "lang": "en-IN",
            "sensitivity": "standard",
            "speed": 4.0,
        })

        ready = ws.receive_json()
        assert ready["type"] == "ready"
        assert "providers" in ready


def test_ws_session_upload_mode():
    with client.websocket_connect("/ws/session") as ws:
        # Send start message with upload mode
        ws.send_json({
            "type": "start",
            "mode": "upload",
            "job_id": "nonexistent_job",
            "lang": "en-IN",
            "sensitivity": "standard",
            "speed": 4.0,
        })

        ready = ws.receive_json()
        assert ready["type"] == "ready"
        assert "providers" in ready


def test_ws_session_malformed_message():
    with client.websocket_connect("/ws/session") as ws:
        # Send valid start message
        ws.send_json({
            "type": "start",
            "mode": "live",
            "lang": "en-IN",
            "sensitivity": "standard",
        })
        ready = ws.receive_json()
        assert ready["type"] == "ready"

        # Send invalid JSON text frame
        ws.send_text("INVALID_NOT_JSON")

        # The server responds with message_error or partial from mock
        received_types = []
        for _ in range(5):
            msg = ws.receive_json()
            received_types.append(msg.get("type"))
            if msg.get("type") == "error":
                assert msg.get("code") in ("validation_error", "message_error")
                break
        assert "error" in received_types or "partial" in received_types


def test_ws_drill_session():
    with client.websocket_connect("/ws/drill") as ws:
        # Send start message for drill
        ws.send_json({
            "type": "start",
            "mode": "drill",
            "scenario_id": "courier-customs-en-01",
            "lang": "en-IN",
            "sensitivity": "standard",
        })

        # Expect ready event
        ready = ws.receive_json()
        assert ready["type"] == "ready"

        # Expect first caller line
        caller_msg = ws.receive_json()
        assert caller_msg["type"] == "caller"
        assert "text" in caller_msg

        # Send user response via chip
        ws.send_json({
            "type": "chip",
            "act": "hangup",
        })

        # Expect ended event
        reply = ws.receive_json()
        assert reply["type"] in ("caller", "ended", "closed")
