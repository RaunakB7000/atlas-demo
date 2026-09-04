import random
from typing import Any

from ..schemas.resource import ResourceStatus, ResourceType

RESOURCE_CONFIG = {
    ResourceType.AMBULANCE: {"count": 15, "speed_mph": 45},
    ResourceType.FIRE_TRUCK: {"count": 8, "speed_mph": 40},
    ResourceType.POLICE: {"count": 20, "speed_mph": 50},
    ResourceType.AIR_AMBULANCE: {"count": 2, "speed_mph": 120},
}

STATION_LOCATIONS = {
    "Fire Station 1": {"lat": 33.4186, "lng": -111.9332},
    "Fire Station 2": {"lat": 33.4056, "lng": -111.9400},
    "Hospital 1": {"lat": 33.4255, "lng": -111.9400},
    "Hospital 2": {"lat": 33.4100, "lng": -111.9350},
    "Police HQ": {"lat": 33.4150, "lng": -111.9375},
}

HOSPITAL_SEED = [
    {
        "id": "hospital_banner_tempe",
        "name": "Banner Desert Tempe",
        "lat": 33.4255,
        "lng": -111.9400,
        "capacity": 18,
        "occupancy": 11,
    },
    {
        "id": "hospital_south",
        "name": "Tempe South Medical",
        "lat": 33.4100,
        "lng": -111.9350,
        "capacity": 14,
        "occupancy": 12,
    },
    {
        "id": "hospital_asu",
        "name": "ASU Health Pavilion",
        "lat": 33.4180,
        "lng": -111.9280,
        "capacity": 10,
        "occupancy": 4,
    },
]


def generate_resources() -> list[dict[str, Any]]:
    resources = []
    for resource_type, config in RESOURCE_CONFIG.items():
        for index in range(config["count"]):
            if resource_type == ResourceType.AMBULANCE:
                station = random.choice(["Hospital 1", "Hospital 2"])
            elif resource_type == ResourceType.FIRE_TRUCK:
                station = random.choice(["Fire Station 1", "Fire Station 2"])
            elif resource_type == ResourceType.AIR_AMBULANCE:
                station = "Hospital 1"
            else:
                station = "Police HQ"
            jitter = 0.004
            base = STATION_LOCATIONS[station]
            resources.append(
                {
                    "id": f"{resource_type.value.replace(' ', '_')}_{index + 1}",
                    "type": resource_type.value,
                    "location": {
                        "lat": round(base["lat"] + random.uniform(-jitter, jitter), 6),
                        "lng": round(base["lng"] + random.uniform(-jitter, jitter), 6),
                    },
                    "status": ResourceStatus.AVAILABLE.value,
                    "speed_mph": config["speed_mph"],
                    "current_incident_id": None,
                    "station": station,
                    "eta": None,
                }
            )
    return resources


def generate_traffic_conditions() -> dict[str, Any]:
    return {
        "road_closures": [
            {
                "location": {"lat": 33.4200, "lng": -111.9350},
                "reason": "Accident",
                "severity": "High",
            }
        ],
        "congestion_areas": [
            {
                "polygon": [
                    [33.4150, -111.9400],
                    [33.4150, -111.9300],
                    [33.4200, -111.9300],
                    [33.4200, -111.9400],
                ],
                "delay_minutes": 8,
            }
        ],
    }
