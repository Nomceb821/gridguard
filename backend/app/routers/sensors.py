from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.sensor_simulator import manager

router = APIRouter(tags=["sensors"])


@router.websocket("/ws/sensors")
async def sensor_feed(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # This endpoint only pushes events; it doesn't expect messages in,
            # but we still need to await something to detect disconnects.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)