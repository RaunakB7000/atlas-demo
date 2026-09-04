from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database.session import get_db
from ..models.hospital import Hospital
from ..models.incident import Incident
from ..models.prediction import Prediction
from ..models.resource import Resource
from ..schemas.incident import IncidentUpdate
from ..schemas.response import ApiMessage
from ..services.call_processor import record_to_incident
from ..services.simulation_engine import simulation
from ..simulator.call_streamer import public_scenarios

router = APIRouter(prefix="/api")


class SimulationStartRequest(BaseModel):
    num_calls: Optional[int] = None
    delay: Optional[float] = None
    scenario: Optional[str] = None


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "atlas"}


@router.get("/incidents")
def list_incidents(db: Session = Depends(get_db)) -> list[dict]:
    return [record_to_incident(row).model_dump() for row in db.query(Incident).all()]


@router.get("/incidents/{incident_id}")
def get_incident(incident_id: str, db: Session = Depends(get_db)) -> dict:
    row = db.query(Incident).filter(Incident.id == incident_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Incident not found")
    return record_to_incident(row).model_dump()


@router.patch("/incidents/{incident_id}")
def update_incident(incident_id: str, payload: IncidentUpdate, db: Session = Depends(get_db)) -> dict:
    row = db.query(Incident).filter(Incident.id == incident_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Incident not found")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(row, key, value.value if hasattr(value, "value") else value)
    db.commit()
    return record_to_incident(row).model_dump()


@router.post("/incidents/{incident_id}/approve")
async def approve_incident(incident_id: str) -> dict:
    result = await simulation.approve_incident(incident_id)
    if result.get("message") == "Incident not found":
        raise HTTPException(status_code=404, detail="Incident not found")
    return result


@router.get("/resources")
def list_resources(db: Session = Depends(get_db)) -> list[dict]:
    return [
        {
            "id": row.id,
            "type": row.type,
            "location": {"lat": row.lat, "lng": row.lng},
            "status": row.status,
            "speed_mph": row.speed_mph,
            "station": row.station,
            "current_incident_id": row.current_incident_id,
            "eta": row.eta,
        }
        for row in db.query(Resource).all()
    ]


@router.get("/hospitals")
def list_hospitals(db: Session = Depends(get_db)) -> list[dict]:
    return [
        {
            "id": row.id,
            "name": row.name,
            "location": {"lat": row.lat, "lng": row.lng},
            "capacity": row.capacity,
            "occupancy": row.occupancy,
            "available_beds": max(row.capacity - row.occupancy, 0),
        }
        for row in db.query(Hospital).all()
    ]


@router.get("/predictions")
def list_predictions(db: Session = Depends(get_db)) -> list[dict]:
    return [
        {
            "id": row.id,
            "label": row.label,
            "lat": row.lat,
            "lng": row.lng,
            "hour": row.hour,
            "probability": row.probability,
            "recommendation": row.recommendation,
        }
        for row in db.query(Prediction).all()
    ]


@router.get("/stats")
def get_stats() -> dict:
    return simulation.snapshot()["stats"]


@router.get("/snapshot")
def get_snapshot() -> dict:
    return simulation.snapshot()


@router.get("/simulation/status")
def simulation_status() -> dict:
    return simulation.status_payload()


@router.get("/simulation/scenarios")
def simulation_scenarios() -> list[dict]:
    return public_scenarios()


@router.post("/simulation/start")
async def start_simulation(payload: Optional[SimulationStartRequest] = None) -> dict:
    payload = payload or SimulationStartRequest()
    return await simulation.start(payload.num_calls, payload.delay, payload.scenario)


@router.post("/simulation/pause")
async def pause_simulation() -> dict:
    return await simulation.pause()


@router.post("/simulation/reset")
async def reset_simulation() -> dict:
    return await simulation.reset()


@router.post("/simulation/inject")
async def inject_critical() -> dict:
    return await simulation.inject_critical()


@router.get("/report")
def report() -> ApiMessage:
    snapshot = simulation.snapshot()
    return ApiMessage(message="After-action report", data=snapshot["after_action_report"])
