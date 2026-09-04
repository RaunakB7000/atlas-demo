from __future__ import annotations

from ..schemas.incident import IncidentResponse, IncidentType, SeverityLevel, get_severity_value
from ..schemas.resource import ResourceResponse, ResourceStatus, ResourceType
from .routing_agent import RoutingAgent


class AllocationAgent:
    """Recommends units from severity, travel time, skills, and hospital load."""

    def __init__(self) -> None:
        self.router = RoutingAgent()

    def required_types(self, incident: IncidentResponse) -> list[ResourceType]:
        text = incident.transcript.lower()
        if incident.incident_type == IncidentType.MEDICAL:
            types = [ResourceType.AMBULANCE]
            if any(token in text for token in ["cardiac", "unconscious", "not responding"]):
                types.insert(0, ResourceType.AIR_AMBULANCE)
            return types
        if incident.incident_type == IncidentType.FIRE:
            return [ResourceType.FIRE_TRUCK, ResourceType.AMBULANCE]
        if incident.incident_type == IncidentType.ACCIDENT:
            types = [ResourceType.POLICE]
            if any(token in text for token in ["injuries", "multi", "three-car", "rollover"]):
                types.extend([ResourceType.AMBULANCE, ResourceType.FIRE_TRUCK])
            return types
        if incident.incident_type == IncidentType.DISTURBANCE:
            return [ResourceType.POLICE]
        return [ResourceType.POLICE]

    def recommend(
        self,
        incident: IncidentResponse,
        resources: list[ResourceResponse],
        hospitals: list[dict] | None = None,
        traffic: dict | None = None,
    ) -> dict:
        required = self.required_types(incident)
        available = [item for item in resources if item.status == ResourceStatus.AVAILABLE]
        ranked = []
        candidate_pool = []
        for resource_type in required:
            candidates = [item for item in available if item.type == resource_type]
            if not candidates and incident.severity == SeverityLevel.P1:
                candidates = available
            scored = []
            for candidate in candidates:
                eta = self.router.eta_minutes(candidate.location, incident.location, candidate.speed_mph, traffic)
                scored.append((eta, candidate))
                candidate_pool.append((eta, candidate, resource_type))
            if scored:
                scored.sort(key=lambda row: row[0])
                ranked.append(
                    {
                        "resource_id": scored[0][1].id,
                        "resource_type": scored[0][1].type.value,
                        "eta": scored[0][0],
                    }
                )
                available = [item for item in available if item.id != scored[0][1].id]

        hospital = self._nearest_hospital(incident, hospitals or [])
        primary = ranked[0]["resource_id"] if ranked else None
        label = ranked[0]["resource_id"].replace("_", " ") if primary else "No unit available"
        primary_resource = next((item for item in resources if item.id == primary), None)
        primary_eta = ranked[0]["eta"] if ranked else None
        urgency = {"P1": 100, "P2": 82, "P3": 64, "P4": 42}.get(
            get_severity_value(incident.severity), 42
        )
        compatibility = 100 if primary_resource and primary_resource.type == required[0] else 78
        eta_score = max(20, round(100 - (primary_eta or 10) * 9)) if primary else 0
        confidence = round((compatibility * 0.45 + eta_score * 0.35 + urgency * 0.20) / 100, 2)
        alternatives = []
        seen = {primary}
        for eta, candidate, matched_type in sorted(candidate_pool, key=lambda row: row[0]):
            if candidate.id in seen:
                continue
            seen.add(candidate.id)
            alternatives.append(
                {
                    "resource_id": candidate.id,
                    "resource_type": candidate.type.value,
                    "eta": eta,
                    "reason": f"Available {matched_type.value.lower()} with a longer estimated arrival time.",
                }
            )
            if len(alternatives) == 3:
                break

        explanation = {
            "summary": (
                f"{label} is the fastest available unit matching the primary response need."
                if primary
                else "No compatible unit is currently available."
            ),
            "confidence": confidence,
            "selected_eta": primary_eta,
            "policy": "Severity first, then capability match, availability, travel time, and receiving capacity.",
            "factors": [
                {
                    "label": "Capability match",
                    "value": primary_resource.type.value if primary_resource else "Unavailable",
                    "score": compatibility if primary else 0,
                    "detail": f"Primary response need: {required[0].value}.",
                },
                {
                    "label": "Estimated arrival",
                    "value": f"{primary_eta} min" if primary_eta is not None else "—",
                    "score": eta_score,
                    "detail": "Includes the current synthetic congestion and closure penalties.",
                },
                {
                    "label": "Incident priority",
                    "value": get_severity_value(incident.severity),
                    "score": urgency,
                    "detail": "Higher-acuity incidents receive a larger allocation weight.",
                },
                {
                    "label": "Receiving capacity",
                    "value": hospital["name"] if hospital else "Not required",
                    "score": 90 if hospital else 75,
                    "detail": (
                        f"{max(hospital['capacity'] - hospital['occupancy'], 0)} beds currently open."
                        if hospital
                        else "No hospital routing is required for this recommendation."
                    ),
                },
            ],
        }
        return {
            "primary_resource_id": primary,
            "recommended_response": label,
            "assignments": ranked,
            "hospital": hospital,
            "explanation": explanation,
            "alternatives": alternatives,
        }

    def _nearest_hospital(self, incident: IncidentResponse, hospitals: list[dict]) -> dict | None:
        if not hospitals:
            return None
        open_hospitals = [item for item in hospitals if item["occupancy"] < item["capacity"]]
        pool = open_hospitals or hospitals
        return min(
            pool,
            key=lambda item: self.router.eta_minutes(
                incident.location,
                {"lat": item["lat"], "lng": item["lng"]},
                35,
            ),
        )
