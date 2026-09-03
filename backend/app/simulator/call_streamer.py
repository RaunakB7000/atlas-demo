import random
import time
from datetime import datetime, timedelta
from typing import Generator, Dict, Any
from faker import Faker
from ..models.incident import Location

fake = Faker()

# Tempe/Phoenix area coordinates (bounding box)
TEMPE_LAT_RANGE = (33.35, 33.45)
TEMPE_LNG_RANGE = (-111.98, -111.88)

# Incident types and their likelihood
INCIDENT_TYPES = {
    "Medical": 0.4,
    "Fire": 0.2,
    "Accident": 0.3,
    "Disturbance": 0.1
}

# Common phrases for each incident type
INCIDENT_PHRASES = {
    "Medical": [
        "chest pain",
        "unconscious",
        "not breathing",
        "cardiac arrest",
        "seizure",
        "diabetic emergency",
        "allergic reaction",
        "stroke symptoms"
    ],
    "Fire": [
        "smoke coming from",
        "building on fire",
        "apartment fire",
        "car fire",
        "explosion",
        "gas leak",
        "electrical fire"
    ],
    "Accident": [
        "car crash",
        "multi-vehicle collision",
        "hit and run",
        "pedestrian struck",
        "motorcycle accident",
        "bicycle accident",
        "rollover accident"
    ],
    "Disturbance": [
        "loud noise",
        "suspicious person",
        "fight in progress",
        "shots fired",
        "domestic dispute",
        "burglary",
        "robbery"
    ]
}

# Common street names in Tempe/Phoenix
TEMPE_STREETS = [
    "Rural Rd", "University Dr", "Apache Blvd", "Mill Ave",
    "Broadway Rd", "Southern Ave", "McClintock Dr", "Priest Dr"
]

def generate_call(call_id: int) -> Dict[str, Any]:
    """Generate a single synthetic 911 call with realistic details."""
    # Random incident type (weighted)
    incident_type = random.choices(
        list(INCIDENT_TYPES.keys()),
        weights=list(INCIDENT_TYPES.values()),
        k=1
    )[0]

    # Random location in Tempe/Phoenix
    location = Location(
        lat=round(random.uniform(*TEMPE_LAT_RANGE), 6),
        lng=round(random.uniform(*TEMPE_LNG_RANGE), 6)
    )

    # Generate realistic transcript
    phrase = random.choice(INCIDENT_PHRASES[incident_type])
    street = random.choice(TEMPE_STREETS)
    address = f"{random.randint(100, 9999)} {street}, Tempe, AZ"

    # Add more context based on incident type
    if incident_type == "Medical":
        transcript = f"Caller reports {phrase}. {fake.sentence()} At {address}."
    elif incident_type == "Fire":
        transcript = f"{fake.sentence()} There's {phrase} at {address}."
    elif incident_type == "Accident":
        transcript = f"{phrase} reported at {address}. {fake.sentence()}"
    else:  # Disturbance
        transcript = f"{fake.sentence()} {phrase} near {address}."

    # Random timestamp (last 2 hours)
    timestamp = datetime.now() - timedelta(
        minutes=random.randint(0, 120)
    )

    return {
        "id": call_id,
        "transcript": transcript,
        "timestamp": timestamp.isoformat(),
        "location": {"lat": location.lat, "lng": location.lng},
        "incident_type": incident_type,  # Ground truth for demo
        "raw_audio_url": f"https://example.com/audio/{call_id}.wav"  # Mock audio
    }

def stream_calls(
    num_calls: int = 500,
    delay: float = 0.1,
    batch_size: int = 5,
    incident_distribution: Dict[str, float] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream synthetic 911 calls with configurable parameters.

    Args:
        num_calls: Total calls to generate (default: 500)
        delay: Seconds between batches (default: 0.1)
        batch_size: Calls per batch (default: 5)
        incident_distribution: Custom incident type weights (optional)

    Yields:
        Dict: Synthetic call data with all fields
    """
    # Use custom distribution if provided
    global INCIDENT_TYPES
    if incident_distribution:
        INCIDENT_TYPES = incident_distribution

    for i in range(0, num_calls, batch_size):
        batch = []
        for j in range(batch_size):
            if i + j >= num_calls:
                break
            batch.append(generate_call(i + j))

        for call in batch:
            yield call

        time.sleep(delay)  # Simulate real-time streaming

def generate_historical_data(
    num_days: int = 7,
    calls_per_day: int = 100
) -> list[Dict[str, Any]]:
    """
    Generate historical call data for training/prediction models.

    Args:
        num_days: Number of days to generate data for
        calls_per_day: Average calls per day

    Returns:
        List of historical call records
    """
    historical_data = []
    base_date = datetime.now() - timedelta(days=num_days)

    for day in range(num_days):
        day_date = base_date + timedelta(days=day)
        calls_today = random.randint(calls_per_day - 20, calls_per_day + 20)

        for call_id in range(calls_today):
            # Adjust incident distribution based on time of day
            hour = random.randint(0, 23)
            if 22 <= hour <= 4:  # Nighttime - more disturbances
                temp_dist = {"Medical": 0.3, "Fire": 0.1, "Accident": 0.2, "Disturbance": 0.4}
            else:  # Daytime - more accidents
                temp_dist = {"Medical": 0.4, "Fire": 0.2, "Accident": 0.3, "Disturbance": 0.1}

            call = generate_call((day * calls_per_day) + call_id)
            call["timestamp"] = (day_date + timedelta(
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )).isoformat()

            # Add weather/traffic context (mock)
            if random.random() > 0.7:
                call["context"] = random.choice([
                    "Heavy rain reported in area",
                    "Major traffic accident nearby",
                    "ASU football game just ended",
                    "Temperature over 110°F"
                ])

            historical_data.append(call)

    return historical_data