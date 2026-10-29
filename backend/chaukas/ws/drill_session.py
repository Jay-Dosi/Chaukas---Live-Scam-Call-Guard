"""Fire-Drill WebSocket session handler — PRD §8.2, §7.3."""

from __future__ import annotations

import asyncio
import time

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from chaukas.drill.classify import classify
from chaukas.drill.machine import DrillState, load_scenario, run_turn
from chaukas.drill.score import calculate_scorecard
from chaukas.drill.debrief import generate_debrief
from chaukas.ws.protocol import (
    ClientMessage,
    ClientStart,
    ClientChip,
    ClientStop,
    client_message_adapter,
    ReadyEvent,
    CallerEvent,
    DrillEndEvent,
    ErrorEvent,
    ClosedEvent,
)


async def handle_drill_session(websocket: WebSocket):
    """Handle Fire-Drill WebSocket session."""
    await websocket.accept()

    try:
        # First message must be start with mode=drill
        raw = await websocket.receive_text()
        try:
            start_data = ClientStart.model_validate_json(raw)
        except ValidationError as e:
            await websocket.send_json(ErrorEvent(code="invalid_start", message=str(e)).model_dump())
            await websocket.close()
            return

        if start_data.mode != "drill":
            await websocket.send_json(ErrorEvent(code="invalid_mode", message="Expected mode=drill").model_dump())
            await websocket.close()
            return

        # Load scenario
        sc_id = start_data.scenario_id or "digital-arrest-hi-01"
        scenario = load_scenario(sc_id, start_data.lang)

        # Initialize drill state
        state = DrillState(
            scenario=scenario,
            current_node_id=scenario.start,
        )

        # Send ready with disclosure
        disclosure = scenario.disclosure.get(start_data.lang[:2], scenario.disclosure.get("en", "This is a practice call."))
        await websocket.send_json(ReadyEvent(
            type="ready",
            providers={
                "scenario": scenario.id,
                "disclosure": disclosure,
            }
        ).model_dump())

        # Send first caller line
        first_node = scenario.nodes[scenario.start]
        await websocket.send_json(CallerEvent(
            type="caller",
            node_id=scenario.start,
            text=first_node.text,
            tactics=first_node.tactics,
            audio_url=f"/api/audio/{scenario.id}/{scenario.start}.wav",
            pressure=0,
        ).model_dump())

        # Main loop
        while True:
            msg = await websocket.receive()
            if "text" in msg:
                data = client_message_adapter.validate_json(msg["text"])

                if data.type == "chip":
                    # Process chip response
                    state, result = run_turn(state, "", start_data.lang, data.act)
                    await _send_result(websocket, state, result, scenario, start_data.lang)
                    if result and result.get("ended"):
                        break

                elif data.type == "text":
                    # Process spoken or typed user text
                    state, result = run_turn(state, data.text, start_data.lang)
                    await _send_result(websocket, state, result, scenario, start_data.lang)
                    if result and result.get("ended"):
                        break

                elif data.type == "stop":
                    # User invoked stop or stop word
                    terminal_result = {
                        "ended": True,
                        "outcome": "safe",
                        "debrief_key": "good_hangup",
                    }
                    state.ended_call_or_refused_hard = True
                    await _send_result(websocket, state, terminal_result, scenario, start_data.lang)
                    break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json(ErrorEvent(code="server_error", message=str(e)).model_dump())
        except Exception:
            pass
    finally:
        try:
            await websocket.send_json(ClosedEvent(type="closed").model_dump())
            await websocket.close()
        except Exception:
            pass


async def _send_result(
    websocket: WebSocket,
    state: DrillState,
    result: dict | None,
    scenario,
    lang: str,
):
    """Send drill turn result to client."""
    if result is None:
        return

    if result.get("ended"):
        # Final debrief
        scorecard = calculate_scorecard({
            "ended_call_or_refused_hard": state.ended_call_or_refused_hard,
            "verified_independently": state.verified_independently,
            "asked_before_complying": state.asked_before_complying,
            "gave_credential_digits": state.gave_credential_digits,
            "agreed_to_transfer": state.agreed_to_transfer,
            "stayed_on_isolating_call": state.stayed_on_isolating_call,
            "genuine_call": scenario.label == "genuine",
            "hung_up_on_genuine_without_verifying": False,  # TODO
        })

        debrief = generate_debrief(
            result["outcome"],
            result["debrief_key"],
            lang[:2],
            state.history,
            {
                "total": scorecard.total,
                "items": [{"label": i.label, "points": i.points} for i in scorecard.items],
                "outcome": scorecard.outcome,
            },
        )

        await websocket.send_json(DrillEndEvent(
            type="ended",
            outcome=result["outcome"],
            scorecard={
                "total": scorecard.total,
                "items": [{"label": i.label, "points": i.points} for i in scorecard.items],
                "outcome": scorecard.outcome,
            },
            debrief=debrief,
        ).model_dump())
    else:
        # Next caller line
        await websocket.send_json(CallerEvent(
            type="caller",
            node_id=result["node_id"],
            text=result["text"],
            tactics=result["tactics"],
            audio_url=f"/api/audio/{scenario.id}/{result['node_id']}.wav",
            pressure=result["pressure"],
        ).model_dump())