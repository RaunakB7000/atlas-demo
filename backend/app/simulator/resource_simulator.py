import random
from typing import List, Dict
from ..models.resource import Resource, ResourceType, ResourceStatus

# Resource configurations
RESOURCE_CONFIG = {
    ResourceType.AMBULANCE: {"count": 15, "speed_mph": 45},
    ResourceType.FIRE_TRUCK: {"count": 8, "speed_mph": 40},
    ResourceType.POLICE: {"count": 20, "speed_mph": 50},
    ResourceType.AIR_AMBULANCE: {"count": 2, "speed_mph": 120}
}

# Initial locations (fire stations, hospitals, police stations)
STATION_LOCATIONS = {
    "Fire Station 1": {"lat": 33.4186, "lng": -111.9332},
    "Fire Station 2": {"lat": 33.4056, "lng": -111.9400},
    "Hospital 1": {"lat": 33.4255, "lng": -111.9400},
    "Hospital 2": {"lat": 33.4100, "lng": -111.9350},
    "Police HQ": {"lat": 33.4150, "lng": -111.9375}
}

def generate_resources() -> List[Resource]:
    """Generate initial resource pool."""
    resources = []
    resource_id = 1

    for resource_type, config in RESOURCE_CONFIG.items():
        for i in range(config["count"]):
            # Assign to nearest station
            if resource_type == ResourceType.AMBULANCE:
                station = random.choice(["Hospital 1", "Hospital 2"])
            elif resource_type == ResourceType.FIRE_TRUCK:
                station = random.choice(["Fire Station 1", "Fire Station 2"])
            else:
                station = "Police HQ"

            resources.append(Resource(
                id=f"{resource_type.value}_{i+1}",
                type=resource_type,
                location=STATION_LOCATIONS[station],
                status=ResourceStatus.AVAILABLE,
                speed_mph=config["speed_mph"],
                current_incident_id=None,
                station=station
            ))
            resource_id += 1

    return resources

def simulate_resource_movement(
    resources: List[Resource],
    incidents: List[Dict],
    time_step: float = 0.5
) -> List[Resource]:
    """
    Simulate resource movement toward incidents.

    Args:
        resources: Current resource states
        incidents: Active incidents
        time_step: Simulation time step in minutes

    Returns:
        Updated resources with new locations
    """
    updated_resources = []

    for resource in resources:
        if resource.status != ResourceStatus.EN_ROUTE:
            updated_resources.append(resource)
            continue

        # Find assigned incident
        incident = next((i for i in incidents if i["id"] == resource.current_incident_id), None)
        if not incident:
            resource.status = ResourceStatus.AVAILABLE
            updated_resources.append(resource)
            continue

        # Calculate movement (simplified)
        lat_diff = incident["location"]["lat"] - resource.location["lat"]
        lng_diff = incident["location"]["lng"] - resource.location["lng"]

        # Convert speed to degrees per minute (approx)
        speed_deg_per_min = resource.speed_mph / 40  # Rough conversion

        # Update location
        new_lat = resource.location["lat"] + (lat_diff * speed_deg_per_min * time_step / 10)
        new_lng = resource.location["lng"] + (lng_diff * speed_deg_per_min * time_step / 10)

        # Check if arrived
        if (abs(lat_diff) < 0.0001 and abs(lng_diff) < 0.0001):
            resource.status = ResourceStatus.ON_SCENE
            resource.location = incident["location"]
        else:
            resource.location = {"lat": new_lat, "lng": new_lng}

        updated_resources.append(resource)

    return updated_resources

def generate_traffic_conditions() -> Dict:
    """Generate mock traffic conditions."""
    return {
        "road_closures": [
            {
                "location": {"lat": 33.4200, "lng": -111.9350},
                "reason": "Accident",
                "severity": "High"
            }
        ],
        "congestion_areas": [
            {
                "polygon": [
                    [33.4150, -111.9400],
                    [33.4150, -111.9300],
                    [33.4200, -111.9300],
                    [33.4200, -111.9400]
                ],
                "delay_minutes": 15
            }
        ]
    }