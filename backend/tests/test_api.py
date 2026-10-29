"""Unit tests for REST API endpoints — PRD §8.2."""

import io
from fastapi.testclient import TestClient
from chaukas.main import app

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == "0.1.0"
    assert "stt" in data
    assert "tts" in data
    assert "llm" in data


def test_scenarios_endpoint():
    resp = client.get("/api/scenarios")
    assert resp.status_code == 200
    scenarios = resp.json()
    assert isinstance(scenarios, list)
    assert len(scenarios) > 0
    first = scenarios[0]
    assert "id" in first
    assert "title" in first
    assert "tactics" in first


def test_benchmark_endpoint():
    resp = client.post("/api/benchmark", json={"noise_wer": 0.0, "sensitivity": "standard"})
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert "cases" in data
    assert "sweep" in data
    assert "per_tactic" in data
    assert data["summary"]["recall_at_danger"] >= 0.92
    assert data["summary"]["false_alarm_rate"] <= 0.05


def test_tts_endpoint_returns_valid_response():
    resp = client.post("/api/tts", json={"text": "Warning, possible scam", "lang": "en"})
    # Either 200 with audio/wav, or 204 if tts_provider is none
    assert resp.status_code in (200, 204)
    if resp.status_code == 200:
        assert resp.headers["content-type"] == "audio/wav"
        assert len(resp.content) > 0


def test_upload_endpoint():
    # Create fake WAV file
    fake_wav = io.BytesIO(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00")
    files = {"file": ("test.wav", fake_wav, "audio/wav")}
    resp = client.post("/api/upload", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data


def test_bolna_call_unconfigured():
    # If Bolna is not configured in test environment, should return 400
    resp = client.post("/api/bolna/call", json={"recipient_phone_number": "+919876543210"})
    assert resp.status_code == 400
    assert "Bolna AI integration is not configured" in resp.json()["detail"]
