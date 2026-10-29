"""Bolna AI Telephony Integration — Outbound drill calls to real phones."""

from __future__ import annotations

import json
import logging
from pathlib import Path
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from chaukas.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "scenarios"


class BolnaCallRequest(BaseModel):
    recipient_phone_number: str = Field(
        ...,
        description="E.164 phone number, e.g. +919876543210",
        examples=["+919876543210"],
    )
    scenario_id: str = Field(
        default="courier-customs-en-01",
        description="Scenario to practice against",
    )


class BolnaCallResponse(BaseModel):
    status: str
    execution_id: str
    message: str


@router.post("/bolna/call", response_model=BolnaCallResponse)
async def trigger_bolna_call(req: BolnaCallRequest):
    """Trigger an outbound telephony call to a mobile phone via Bolna AI API."""
    settings = get_settings()

    if not settings.bolna_api_key or not settings.bolna_agent_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "Bolna AI integration is not configured. "
                "Please add BOLNA_API_KEY and BOLNA_AGENT_ID to your .env file."
            ),
        )

    # Validate phone number basic format (+ and at least 10 digits)
    phone = req.recipient_phone_number.strip().replace(" ", "").replace("-", "")
    if not phone.startswith("+") or len(phone) < 11:
        raise HTTPException(
            status_code=422,
            detail="Phone number must be in international E.164 format with country code (e.g. +919876543210).",
        )

    # Lookup scenario details if available
    scenario_title = req.scenario_id
    try:
        sc_file = SCENARIOS_DIR / f"{req.scenario_id}.json"
        if sc_file.exists():
            with open(sc_file, encoding="utf-8") as f:
                sc_data = json.load(f)
            scenario_title = sc_data.get("title", req.scenario_id)
    except Exception:
        pass

    url = "https://api.bolna.ai/call"
    headers = {
        "Authorization": f"Bearer {settings.bolna_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "agent_id": settings.bolna_agent_id,
        "recipient_phone_number": phone,
        "user_data": {
            "scenario_id": req.scenario_id,
            "scenario_title": scenario_title,
            "app": "Chaukas Scam Guard",
        },
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code >= 400:
                logger.error(f"Bolna API error ({resp.status_code}): {resp.text}")
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"Bolna API rejected request: {resp.text}",
                )
            data = resp.json()
            execution_id = str(data.get("execution_id") or data.get("id") or "")
            return BolnaCallResponse(
                status="queued",
                execution_id=execution_id,
                message=f"Outbound phone call initiated to {phone}! Answer on speakerphone and let Chaukas listen.",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to connect to Bolna API")
        raise HTTPException(
            status_code=502,
            detail=f"Network error contacting Bolna API: {str(e)}",
        )
