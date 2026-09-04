from typing import Any, Optional

from pydantic import BaseModel, Field


class ApiMessage(BaseModel):
    message: str
    data: Optional[dict[str, Any]] = None


class SimulationStatus(BaseModel):
    state: str
    incoming_reports: int = 0
    transcribed: int = 0
    unique_incidents: int = 0
    critical: int = 0
    high_priority: int = 0
    medium: int = 0
    low: int = 0
    target_calls: int = 0
    last_event: Optional[str] = None


class PredictionResponse(BaseModel):
    id: int
    label: str
    lat: float
    lng: float
    hour: int
    probability: float
    recommendation: Optional[str] = None


class ReallocationEvent(BaseModel):
    message: str
    incident_id: str
    changes: list[dict[str, Any]] = Field(default_factory=list)
