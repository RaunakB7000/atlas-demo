from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from ..schemas.incident import Location


HOTSPOTS = [
    {
        "label": "Mill Avenue entertainment district",
        "lat": 33.4255,
        "lng": -111.9400,
        "hours": {22, 23, 0, 1},
        "boost": 0.28,
        "recommendation": "Pre-position 2 ambulances and 1 police unit near Mill Ave.",
    },
    {
        "label": "Rural and Broadway corridor",
        "lat": 33.4070,
        "lng": -111.9260,
        "hours": {16, 17, 18},
        "boost": 0.18,
        "recommendation": "Stage a crash-response unit for evening commute.",
    },
    {
        "label": "ASU campus edge",
        "lat": 33.4186,
        "lng": -111.9332,
        "hours": {11, 12, 21, 22},
        "boost": 0.14,
        "recommendation": "Keep one ALS ambulance on campus standby.",
    },
]


class PredictionAgent:
    """Spatiotemporal demand forecast from historical synthetic 911 volume."""

    def forecast(self, historical: list[dict], hour: int | None = None) -> list[dict]:
        hour = datetime.now().hour if hour is None else hour
        buckets: dict[str, list[dict]] = defaultdict(list)
        for record in historical:
            try:
                timestamp = datetime.fromisoformat(record["timestamp"])
            except (KeyError, ValueError):
                continue
            if abs(timestamp.hour - hour) <= 1:
                buckets[record.get("incident_type", "Other")].append(record)

        predictions = []
        for index, hotspot in enumerate(HOTSPOTS, start=1):
            nearby = 0
            for records in buckets.values():
                nearby += sum(
                    1
                    for item in records
                    if abs(item["location"]["lat"] - hotspot["lat"]) < 0.012
                    and abs(item["location"]["lng"] - hotspot["lng"]) < 0.012
                )
            base = min(0.35 + nearby * 0.03, 0.7)
            if hour in hotspot["hours"]:
                base += hotspot["boost"]
            predictions.append(
                {
                    "id": index,
                    "label": hotspot["label"],
                    "lat": hotspot["lat"],
                    "lng": hotspot["lng"],
                    "hour": hour,
                    "probability": round(min(base, 0.95), 2),
                    "recommendation": hotspot["recommendation"],
                    "location": Location(lat=hotspot["lat"], lng=hotspot["lng"]).model_dump(),
                }
            )
        return sorted(predictions, key=lambda item: item["probability"], reverse=True)
