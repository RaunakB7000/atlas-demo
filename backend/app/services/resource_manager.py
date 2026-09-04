from __future__ import annotations

from ..agents.allocation_agent import AllocationAgent
from ..agents.routing_agent import RoutingAgent
from ..schemas.incident import IncidentResponse, SeverityLevel, get_severity_value
from ..schemas.resource import ResourceResponse, ResourceStatus, ResourceType

def severity_priority(severity: SeverityLevel | str) -> int:
    """Get priority for sorting - lower number = higher priority.
    
    P1 = 1 (highest priority), P2 = 2, P3 = 3, P4 = 4 (lowest priority)
    """
    return {"P1": 1, "P2": 2, "P3": 3, "P4": 4}.get(get_severity_value(severity), 4)


class ResourceManager:
    def __init__(self, initial_resources: list[ResourceResponse] | None = None) -> None:
        self.resources: dict[str, ResourceResponse] = {
            item.id: item for item in (initial_resources or [])
        }
        self.allocator = AllocationAgent()
        self.router = RoutingAgent()

    def load(self, resources: list[ResourceResponse]) -> None:
        self.resources = {item.id: item for item in resources}

    def allocate_resources(
        self,
        incidents: list[IncidentResponse],
        hospitals: list[dict] | None = None,
        traffic: dict | None = None,
    ) -> list[ResourceResponse]:
        sorted_incidents = sorted(
            incidents,
            key=lambda item: (self._severity_priority(item.severity), item.timestamp),
        )
        for incident in sorted_incidents:
            if incident.assigned_resource or incident.status == "Resolved":
                continue
            recommendation = self.allocator.recommend(
                incident,
                list(self.resources.values()),
                hospitals,
                traffic,
            )
            resource_id = recommendation["primary_resource_id"]
            if not resource_id:
                continue
            self.apply_recommendation(incident, recommendation)
        return list(self.resources.values())

    def recommend_only(
        self,
        incident: IncidentResponse,
        hospitals: list[dict] | None = None,
        traffic: dict | None = None,
    ) -> dict:
        return self.allocator.recommend(incident, list(self.resources.values()), hospitals, traffic)

    def apply_recommendation(self, incident: IncidentResponse, recommendation: dict) -> None:
        """Attach one explainable proposal without changing resource state."""
        extra = recommendation.get("assignments", [])[1:]
        incident.context = {
            **incident.context,
            "recommended_resource_id": recommendation.get("primary_resource_id"),
            "recommended_support_units": [row["resource_id"] for row in extra],
            "hospital": recommendation.get("hospital"),
            "recommendation_explanation": recommendation.get("explanation", {}),
            "recommendation_alternatives": recommendation.get("alternatives", []),
        }
        incident.context.pop("support_units", None)
        incident.recommended_response = recommendation["recommended_response"]
        if incident.status in {"Pending", "Clustered", "Awaiting Resource"}:
            incident.status = "Recommended"

    def dispatch_resource(
        self,
        resource_id: str,
        incident: IncidentResponse,
        traffic: dict | None = None,
    ) -> ResourceResponse | None:
        resource = self.resources.get(resource_id)
        if not resource or resource.status != ResourceStatus.AVAILABLE:
            return None
        self._assign_resource(resource, incident, traffic)
        return resource

    def update_resource_status(self) -> None:
        for resource in self.resources.values():
            if resource.status == ResourceStatus.EN_ROUTE and resource.eta is not None:
                resource.eta = max(0, round(resource.eta - 0.4, 1))
                if resource.eta <= 0:
                    resource.status = ResourceStatus.ON_SCENE

    def release_resource(self, resource_id: str) -> None:
        resource = self.resources.get(resource_id)
        if not resource:
            return
        resource.status = ResourceStatus.AVAILABLE
        resource.current_incident_id = None
        resource.eta = None

    def get_resource_utilization(self) -> dict:
        total = len(self.resources)
        available = sum(1 for item in self.resources.values() if item.status == ResourceStatus.AVAILABLE)
        return {
            "total": total,
            "available": available,
            "utilization": 1 - (available / total) if total else 0,
        }

    def _assign_resource(
        self,
        resource: ResourceResponse,
        incident: IncidentResponse,
        traffic: dict | None = None,
    ) -> None:
        resource.status = ResourceStatus.EN_ROUTE
        resource.current_incident_id = incident.id
        resource.eta = self.router.eta_minutes(
            resource.location,
            incident.location,
            resource.speed_mph,
            traffic,
        )
        incident.assigned_resource = resource.id
        incident.status = "Dispatched"
        incident.recommended_response = resource.id.replace("_", " ")

    def _severity_priority(self, severity: SeverityLevel | str) -> int:
        return severity_priority(severity)
