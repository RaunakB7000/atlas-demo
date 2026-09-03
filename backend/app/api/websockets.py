# backend/app/api/websockets.py
from fastapi import WebSocket
from ..services.call_processor import CallProcessor
from ..simulator.call_streamer import stream_calls

processor = CallProcessor()

@router.websocket("/ws/incidents")
async def websocket_incidents(websocket: WebSocket):
    await websocket.accept()
    for call in stream_calls():
        incident = processor.process_call(call)
        await websocket.send_json(incident.dict())