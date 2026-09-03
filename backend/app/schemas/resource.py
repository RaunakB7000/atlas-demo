from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class IncidentType(str, Enum):
    MEDICAL = "Medical"
    FIRE = "Fire"
    ACCIDENT = "Accident"
    DISTURBANCE = "Disturbance"
    OTHER = "Other"

class SeverityLevel(str, Enum):
    P1 = "P1"  # Critical
    P2 = "P2"  # High
    P3 = "P3"  # Medium
    P4 = "P4"  # Low

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
    id: int
    incident_type: IncidentType
    severity: SeverityLevel
    confidence: float
    clustered_calls: Optional[List[int]] = None
    assigned_resource: Optional[str] = None
    status: str = "Pending"
    context: Optional[dict] = None

class IncidentUpdate(BaseModel):
    severity: Optional[SeverityLevel] = None
    assigned_resource: Optional[str] = None
    status: Optional[str] = None

class IncidentCluster(BaseModel):
    cluster_id: int
    incidents: List[IncidentResponse]
    centroid: Location
    confidence: float