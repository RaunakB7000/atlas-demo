from enum import Enum
from typing import Optional

from pydantic import BaseModel

from .incident import Location


class ResourceType(str, Enum):
    AMBULANCE = "Ambulance"
    FIRE_TRUCK = "Fire Truck"
    POLICE = "Police"
    AIR_AMBULANCE = "Air Ambulance"


class ResourceStatus(str, Enum):
    AVAILABLE = "Available"
    EN_ROUTE = "En Route"
    ON_SCENE = "On Scene"
    UNAVAILABLE = "Unavailable"


class ResourceBase(BaseModel):
    type: ResourceType
    location: Location
    speed_mph: int


class ResourceCreate(ResourceBase):
    station: str


class ResourceResponse(ResourceBase):
    id: str
    status: ResourceStatus
    current_incident_id: Optional[str] = None
    station: str
    eta: Optional[float] = None


class ResourceUpdate(BaseModel):
    status: Optional[ResourceStatus] = None
    location: Optional[Location] = None
    current_incident_id: Optional[str] = None


class ResourceAssignment(BaseModel):
    resource_id: str
    incident_id: str


class HospitalResponse(BaseModel):
    id: str
    name: str
    location: Location
    capacity: int
    occupancy: int
    available_beds: int
