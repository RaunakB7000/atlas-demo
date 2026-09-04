from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class IncidentType(str, Enum):
    MEDICAL = "Medical"
    FIRE = "Fire"
    ACCIDENT = "Accident"
    DISTURBANCE = "Disturbance"
    OTHER = "Other"


class SeverityLevel(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"

    @classmethod
    def get_value(cls, severity: SeverityLevel | str) -> str:
        """Get the string value of a severity level.
        
        Handles both SeverityLevel enums and plain strings.
        Returns P1, P2, P3, or P4 consistently.
        """
        if isinstance(severity, SeverityLevel):
            return severity.value
        return str(severity).upper()


def get_severity_value(severity: SeverityLevel | str) -> str:
    """Return the canonical P1-P4 string for enums and plain strings."""
    return SeverityLevel.get_value(severity)


class Location(BaseModel):
    lat: float
    lng: float


class IncidentBase(BaseModel):
    transcript: str
    location: Location
    timestamp: str


class IncidentCreate(IncidentBase):
    pass


class IncidentResponse(IncidentBase):
    id: str
    incident_type: IncidentType
    severity: SeverityLevel
    confidence: float = 0.8
    clustered_calls: list[int] = Field(default_factory=list)
    assigned_resource: Optional[str] = None
    status: str = "Pending"
    context: dict[str, Any] = Field(default_factory=dict)
    recommended_response: Optional[str] = None
    dispatcher_approved: bool = False
    call_count: int = 1


class IncidentUpdate(BaseModel):
    severity: Optional[SeverityLevel] = None
    assigned_resource: Optional[str] = None
    status: Optional[str] = None
    dispatcher_approved: Optional[bool] = None


class IncidentCluster(BaseModel):
    cluster_id: str
    incidents: list[IncidentResponse]
    centroid: Location
    confidence: float
