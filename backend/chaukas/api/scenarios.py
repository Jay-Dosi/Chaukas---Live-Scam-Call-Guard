"""Scenarios API endpoints — PRD §8.2."""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter()

SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "scenarios"


@router.get("/scenarios")
async def list_scenarios():
    """List all scenarios with brief info."""
    scenarios = []
    for path in SCENARIOS_DIR.glob("*.json"):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        scenarios.append({
            "id": data["id"],
            "title": data["title"],
            "lang": data["lang"],
            "label": data["label"],
            "tactics": data["tactics"],
            "expect": data.get("expect", {}),
        })
    return scenarios


@router.get("/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str):
    """Get full scenario including nodes and terminals."""
    path = SCENARIOS_DIR / f"{scenario_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Scenario not found")
    with open(path, encoding="utf-8") as f:
        return json.load(f)