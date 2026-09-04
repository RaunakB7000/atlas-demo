from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..services.simulation_engine import simulation

router = APIRouter()


@router.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    await websocket.accept()
    await simulation.subscribe(websocket)
    try:
        while True:
            message = await websocket.receive_json()
            action = message.get("action")
            if action == "start":
                await simulation.start(message.get("num_calls"), message.get("delay"))
            elif action == "pause":
                await simulation.pause()
            elif action == "reset":
                await simulation.reset()
            elif action == "inject":
                await simulation.inject_critical()
            elif action == "approve":
                await simulation.approve_incident(message.get("incident_id"))
    except WebSocketDisconnect:
        simulation.unsubscribe(websocket)
    except Exception:
        simulation.unsubscribe(websocket)
