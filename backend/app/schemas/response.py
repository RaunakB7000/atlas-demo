from pydantic import BaseModel
from enum import Enum
from typing import Optional

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
    location: dict  # {lat: float, lng: float}
    speed_mph: int

class ResourceCreate(ResourceBase):
    station: str

class ResourceResponse(ResourceBase):
    id: str
    status: ResourceStatus
    current_incident_id: Optional[int] = None
    station: str
    eta: Optional[float] = None  # Minutes

class ResourceUpdate(BaseModel):
    status: Optional[ResourceStatus] = None
    location: Optional[dict] = None
    current_incident_id: Optional[int] = None

class ResourceAssignment(BaseModel):
    resource_id: str
    incident_id: int