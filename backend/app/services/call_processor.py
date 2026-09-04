from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from ..agents.call_understanding import CallUnderstandingAgent
from ..agents.clustering_agent import ClusteringAgent
from ..agents.severity_agent import SeverityAgent
from ..agents.air_client import air_client
from ..schemas.incident import IncidentResponse, IncidentType, Location, SeverityLevel, get_severity_value


def severity_priority(severity: SeverityLevel | str) -> int:
    """Get priority for sorting - lower number = higher priority.
    
    P1 = 1 (highest priority), P2 = 2, P3 = 3, P4 = 4 (lowest priority)
    """
    return {"P1": 1, "P2": 2, "P3": 3, "P4": 4}.get(get_severity_value(severity), 4)


class CallProcessor:
    def __init__(self) -> None:
        self.understanding = CallUnderstandingAgent()
        self.severity = SeverityAgent()
        self.clustering = ClusteringAgent()

    def process_call(self, call_data: dict[str, Any]) -> IncidentResponse:
        deterministic = bool(call_data.get("deterministic"))
        transcript = call_data["transcript"]
        if not deterministic:
            transcript = air_client.transcribe(
                call_data.get("raw_audio_url", ""),
                transcript,
            )
        extracted = self.understanding.analyze(transcript, deterministic=deterministic)
        incident_type = extracted["incident_type"]
        if isinstance(incident_type, str):
            incident_type = IncidentType(incident_type)
        model_incident_type = incident_type
        if deterministic and call_data.get("incident_type"):
            incident_type = IncidentType(str(call_data["incident_type"]).title())
        severity_info = self.severity.recommend(
            transcript,
            incident_type,
            deterministic=deterministic,
        )
        location = call_data["location"]
        if not isinstance(location, Location):
            location = Location(**location)

        incident = IncidentResponse(
            id=f"inc_{call_data['id']}",
            transcript=transcript,
            incident_type=incident_type,
            severity=severity_info["severity"],
            location=location,
            timestamp=call_data.get("timestamp", datetime.now().isoformat()),
            confidence=0.91 if extracted.get("source") == "air" else 0.84,
            clustered_calls=[int(call_data["id"])],
            status="Pending",
            context={
                "signals": extracted.get("signals", []),
                "injuries": extracted.get("injuries", []),
                "hazards": extracted.get("hazards", []),
                "people_count": extracted.get("people_count", 1),
                "address_hint": extracted.get("address_hint", ""),
                "severity_rationale": severity_info["rationale"],
                "escalate": severity_info["escalate"],
                "source": extracted.get("source"),
                "analysis_mode": "validated scenario replay" if deterministic else "live analysis",
                "model_incident_type": model_incident_type.value,
            },
            call_count=1,
        )
        incident.recommended_response = self._default_recommendation(incident)
        return incident

    def merge_into(self, existing: IncidentResponse, incoming: IncidentResponse) -> IncidentResponse:
        previous_status = existing.status
        previous_recommendation = existing.recommended_response
        was_active = bool(existing.assigned_resource) or previous_status in {"Dispatched", "En Route", "On Scene"}
        existing.clustered_calls = list(set(existing.clustered_calls + incoming.clustered_calls))
        existing.call_count = len(existing.clustered_calls)
        # Cluster severity escalates to the most serious severity among its reports
        # P1 (4) > P2 (3) > P3 (2) > P4 (1)
        if severity_priority(incoming.severity) < severity_priority(existing.severity):
            existing.severity = incoming.severity
            existing.transcript = incoming.transcript
        existing.location = self._centroid([existing.location, incoming.location])
        existing.confidence = min(0.98, round(0.78 + 0.04 * existing.call_count, 2))
        existing.status = previous_status if was_active else "Clustered"
        existing.context = {
            **existing.context,
            "original_incidents": existing.call_count,
            "time_span": self._time_span([existing, incoming]),
        }
        existing.recommended_response = previous_recommendation if was_active else self._default_recommendation(existing)
        return existing

    def process_batch(self, calls: list[dict[str, Any]]) -> list[IncidentResponse]:
        incidents = [self.process_call(call) for call in calls]
        clusters = self.clustering.detect(incidents)
        merged = []
        for cluster_id, group in clusters.items():
            if len(group) == 1:
                merged.append(group[0])
            else:
                # Base is the most severe incident in the cluster (lowest priority number)
                base = min(group, key=lambda item: severity_priority(item.severity))
                for extra in group:
                    if extra.id != base.id:
                        base = self.merge_into(base, extra)
                base.id = f"cluster_{cluster_id}"
                merged.append(base)
        return merged

    def _default_recommendation(self, incident: IncidentResponse) -> str:
        mapping = {
            IncidentType.MEDICAL: "Nearest ALS ambulance",
            IncidentType.FIRE: "Fire engine + ambulance",
            IncidentType.ACCIDENT: "Police and rescue",
            IncidentType.DISTURBANCE: "Nearest police unit",
            IncidentType.OTHER: "Nearest available unit",
        }
        return mapping[incident.incident_type]

    def _severity_rank(self, severity: SeverityLevel | str) -> int:
        # For clustering, higher number = more severe (for comparison)
        return {"P1": 4, "P2": 3, "P3": 2, "P4": 1}.get(get_severity_value(severity), 0)

    def _centroid(self, locations: list[Location]) -> Location:
        return Location(
            lat=round(sum(item.lat for item in locations) / len(locations), 6),
            lng=round(sum(item.lng for item in locations) / len(locations), 6),
        )

    def _time_span(self, incidents: list[IncidentResponse]) -> str:
        stamps = [datetime.fromisoformat(item.timestamp.replace("Z", "+00:00")).replace(tzinfo=None) for item in incidents]
        delta = max(stamps) - min(stamps)
        seconds = delta.total_seconds()
        if seconds < 60:
            return f"{int(seconds)} seconds"
        return f"{int(seconds / 60)} minutes"


def incident_to_record(incident: IncidentResponse) -> dict[str, Any]:
    return {
        "id": incident.id,
        "transcript": incident.transcript,
        "incident_type": incident.incident_type.value,
        "severity": get_severity_value(incident.severity),
        "lat": incident.location.lat,
        "lng": incident.location.lng,
        "timestamp": datetime.fromisoformat(incident.timestamp.replace("Z", "+00:00")).replace(tzinfo=None),
        "confidence": incident.confidence,
        "clustered_calls": json.dumps(incident.clustered_calls),
        "assigned_resource": incident.assigned_resource,
        "status": incident.status,
        "context": json.dumps(incident.context),
        "recommended_response": incident.recommended_response,
        "dispatcher_approved": incident.dispatcher_approved,
        "call_count": incident.call_count,
    }


def record_to_incident(record) -> IncidentResponse:
    return IncidentResponse(
        id=record.id,
        transcript=record.transcript,
        incident_type=IncidentType(record.incident_type),
        severity=SeverityLevel(record.severity),
        location=Location(lat=record.lat, lng=record.lng),
        timestamp=record.timestamp.isoformat(),
        confidence=record.confidence,
        clustered_calls=json.loads(record.clustered_calls or "[]"),
        assigned_resource=record.assigned_resource,
        status=record.status,
        context=json.loads(record.context or "{}"),
        recommended_response=record.recommended_response,
        dispatcher_approved=record.dispatcher_approved,
        call_count=record.call_count,
    )
