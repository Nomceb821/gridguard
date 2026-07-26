"""
Simulates motion sensors installed along electrical infrastructure. Since
real sensor hardware isn't available for this project, a background asyncio
task periodically emits either a "normal" reading or an occasional "tamper"
event, broadcasting both over a WebSocket so the dashboard can show a live
feed. A "tamper" event also creates an Alert row and fires notifications --
the same downstream path a real sensor would trigger.
"""

import asyncio
import json
import logging
import random

from fastapi import WebSocket

from app.alerts_service import dispatch_alert
from app.database import SessionLocal
from app.models import Alert, Household

logger = logging.getLogger("gridguard.sensors")

TAMPER_PROBABILITY = 0.08  # chance any given tick is a tamper event
TICK_SECONDS = 6


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, payload: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


async def sensor_loop():
    while True:
        await asyncio.sleep(TICK_SECONDS)
        db = SessionLocal()
        try:
            households = db.query(Household).all()
            if not households:
                continue
            household = random.choice(households)
            is_tamper = random.random() < TAMPER_PROBABILITY

            event = {
                "type": "sensor_event",
                "household_id": household.id,
                "meter_number": household.meter_number,
                "status": "tamper_suspected" if is_tamper else "normal",
            }
            await manager.broadcast(event)

            if is_tamper:
                message = (
                    f"Unusual cable movement detected near meter "
                    f"{household.meter_number} ({household.address})."
                )
                alert = Alert(
                    household_id=household.id,
                    alert_type="sensor_tamper",
                    message=message,
                    severity="high",
                )
                db.add(alert)
                db.commit()
                db.refresh(alert)

                await manager.broadcast({
                    "type": "new_alert",
                    "alert_id": alert.id,
                    "household_id": household.id,
                    "message": message,
                    "severity": "high",
                })

                dispatch_alert(subject="GridGuard: possible cable tampering", body=message)
        except Exception:
            logger.exception("Error in sensor simulation loop")
        finally:
            db.close()