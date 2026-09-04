import random
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator

from ..schemas.incident import Location


SCENARIOS: dict[str, dict[str, Any]] = {
    "asu_game_night": {
        "id": "asu_game_night",
        "label": "ASU game night",
        "description": "Post-event crowd surge across Mill Avenue and the ASU campus edge.",
        "focus": "Crowd safety, medical calls, and traffic incidents",
        "default_calls": 72,
        "seed": 7301,
        "weights": {"Medical": 0.34, "Fire": 0.12, "Accident": 0.26, "Disturbance": 0.28},
    },
    "monsoon_response": {
        "id": "monsoon_response",
        "label": "Monsoon response",
        "description": "A fast-moving storm creates collisions, outages, and access constraints.",
        "focus": "Road access, rescue, and hospital load",
        "default_calls": 64,
        "seed": 8128,
        "weights": {"Medical": 0.25, "Fire": 0.20, "Accident": 0.45, "Disturbance": 0.10},
    },
    "weekday_commute": {
        "id": "weekday_commute",
        "label": "Weekday commute",
        "description": "Morning congestion along Rural Road, Broadway, and the Loop 202.",
        "focus": "Collision clustering and ambulance coverage",
        "default_calls": 56,
        "seed": 4510,
        "weights": {"Medical": 0.30, "Fire": 0.10, "Accident": 0.50, "Disturbance": 0.10},
    },
}

DEFAULT_SCENARIO = "asu_game_night"


def seed_simulation(seed: int) -> None:
    """Seed all synthetic inputs used by a scenario run."""
    random.seed(seed)


def public_scenarios() -> list[dict[str, Any]]:
    return [
        {key: value for key, value in scenario.items() if key != "seed" and key != "weights"}
        for scenario in SCENARIOS.values()
    ]

TEMPE_LAT_RANGE = (33.35, 33.45)
TEMPE_LNG_RANGE = (-111.98, -111.88)

INCIDENT_TYPES = {
    "Medical": 0.4,
    "Fire": 0.2,
    "Accident": 0.3,
    "Disturbance": 0.1,
}

INCIDENT_PHRASES = {
    "Medical": [
        "chest pain",
        "unconscious and not responding",
        "not breathing",
        "possible cardiac arrest",
        "seizure",
        "diabetic emergency",
        "allergic reaction",
        "stroke symptoms",
        "collapsed and unresponsive",
    ],
    "Fire": [
        "smoke coming from an apartment",
        "building on fire",
        "apartment fire",
        "car fire",
        "explosion",
        "gas leak",
        "electrical fire",
    ],
    "Accident": [
        "three-car crash on Rural and Broadway",
        "multi-vehicle collision",
        "hit and run",
        "pedestrian struck",
        "motorcycle accident",
        "huge accident on Mill Ave",
        "car flip near ASU",
    ],
    "Disturbance": [
        "someone is yelling outside but I don't see a weapon",
        "suspicious person",
        "fight in progress",
        "shots fired",
        "domestic dispute",
        "burglary",
        "robbery",
    ],
}

TEMPE_STREETS = [
    "Rural Rd",
    "University Dr",
    "Apache Blvd",
    "Mill Ave",
    "Broadway Rd",
    "Southern Ave",
    "McClintock Dr",
    "Priest Dr",
]

CLUSTER_SEEDS = [
    {
        "incident_type": "Accident",
        "lat": 33.4248,
        "lng": -111.9402,
        "phrase": "huge accident on Mill Ave",
        "street": "Mill Ave",
        "variants": [
            "There's a huge accident on Mill Ave.",
            "Three cars crashed by Mill and University.",
            "I just saw a car flip near ASU.",
        ],
    },
    {
        "incident_type": "Medical",
        "lat": 33.4140,
        "lng": -111.9265,
        "phrase": "possible cardiac arrest",
        "street": "Rural Rd",
        "variants": [
            "My dad collapsed and isn't responding.",
            "Unconscious person, possible cardiac arrest.",
            "He's not breathing on Rural Road.",
        ],
    },
    {
        "incident_type": "Fire",
        "lat": 33.4075,
        "lng": -111.9330,
        "phrase": "smoke coming from an apartment",
        "street": "Broadway Rd",
        "variants": [
            "There's smoke coming from an apartment.",
            "Apartment fire, people still inside.",
            "I see flames on the second floor.",
        ],
    },
]


def generate_call(
    call_id: int,
    force_cluster: bool = True,
    scenario: str = DEFAULT_SCENARIO,
) -> dict[str, Any]:
    scenario_config = SCENARIOS.get(scenario, SCENARIOS[DEFAULT_SCENARIO])
    if force_cluster and call_id % 7 == 0:
        seed = CLUSTER_SEEDS[call_id % len(CLUSTER_SEEDS)]
        jitter = 0.0015
        location = Location(
            lat=round(seed["lat"] + random.uniform(-jitter, jitter), 6),
            lng=round(seed["lng"] + random.uniform(-jitter, jitter), 6),
        )
        transcript = random.choice(seed["variants"])
        address = f"{random.randint(100, 9999)} {seed['street']}, Tempe, AZ"
        transcript = f"{transcript} At {address}."
        incident_type = seed["incident_type"]
    else:
        weights = scenario_config["weights"]
        incident_type = random.choices(
            list(weights.keys()),
            weights=list(weights.values()),
            k=1,
        )[0]
        location = Location(
            lat=round(random.uniform(*TEMPE_LAT_RANGE), 6),
            lng=round(random.uniform(*TEMPE_LNG_RANGE), 6),
        )
        phrase = random.choice(INCIDENT_PHRASES[incident_type])
        street = random.choice(TEMPE_STREETS)
        address = f"{random.randint(100, 9999)} {street}, Tempe, AZ"
        if incident_type == "Medical":
            transcript = f"Caller reports a patient with {phrase} at {address}. Caller is staying on scene."
        elif incident_type == "Fire":
            transcript = f"Multiple callers report {phrase} at {address}. Occupancy is not yet confirmed."
        elif incident_type == "Accident":
            transcript = f"Traffic collision reported: {phrase} at {address}. Lanes may be blocked."
        else:
            transcript = f"Caller reports {phrase} near {address}. No additional hazards confirmed."

    timestamp = datetime.now() - timedelta(seconds=random.randint(0, 90))
    return {
        "id": call_id,
        "transcript": transcript,
        "timestamp": timestamp.isoformat(),
        "location": {"lat": location.lat, "lng": location.lng},
        "incident_type": incident_type,
        "raw_audio_url": f"https://example.com/audio/{call_id}.wav",
        "deterministic": True,
    }


async def stream_calls(
    num_calls: int = 200,
    delay: float = 0.4,
    batch_size: int = 5,
    start_id: int = 1,
    scenario: str = DEFAULT_SCENARIO,
    seed: int | None = None,
) -> AsyncGenerator[list[dict[str, Any]], None]:
    if seed is not None:
        seed_simulation(seed)
    current = start_id
    remaining = num_calls
    while remaining > 0:
        size = min(batch_size, remaining)
        batch = [generate_call(current + offset, scenario=scenario) for offset in range(size)]
        current += size
        remaining -= size
        yield batch


def generate_historical_data(
    num_days: int = 7,
    calls_per_day: int = 80,
    scenario: str = DEFAULT_SCENARIO,
) -> list[dict[str, Any]]:
    historical_data = []
    base_date = datetime.now() - timedelta(days=num_days)
    call_id = 10000
    for day in range(num_days):
        day_date = base_date + timedelta(days=day)
        calls_today = random.randint(calls_per_day - 15, calls_per_day + 15)
        for _ in range(calls_today):
            call = generate_call(call_id, force_cluster=False, scenario=scenario)
            call["timestamp"] = (
                day_date
                + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
            ).isoformat()
            if random.random() > 0.7:
                call["context"] = random.choice(
                    [
                        "Heavy rain reported in area",
                        "Major traffic accident nearby",
                        "ASU football game just ended",
                        "Temperature over 110°F",
                    ]
                )
            historical_data.append(call)
            call_id += 1
    return historical_data


def generate_critical_inject(call_id: int, scenario: str = DEFAULT_SCENARIO) -> dict[str, Any]:
    return {
        "id": call_id,
        "transcript": "Major multi-vehicle collision on the 202 with trapped occupants and a possible cardiac arrest in one vehicle. Rural and Broadway.",
        "timestamp": datetime.now().isoformat(),
        "location": {"lat": 33.4068, "lng": -111.9262},
        "incident_type": "Accident",
        "raw_audio_url": f"https://example.com/audio/{call_id}.wav",
        "injected": True,
        "deterministic": True,
        "context": {"scenario": scenario, "trigger": "guided_replan"},
    }
