from __future__ import annotations

from ..agents.routing_agent import RoutingAgent
from ..schemas.incident import IncidentResponse, SeverityLevel, get_severity_value
from ..schemas.resource import ResourceResponse, ResourceStatus


def severity_rank(severity: SeverityLevel | str) -> int:
    """Get ranking for comparison - higher number = more severe.
    
    P1 = 4 (most severe), P2 = 3, P3 = 2, P4 = 1 (least severe)
    """
    return {"P1": 4, "P2": 3, "P3": 2, "P4": 1}.get(get_severity_value(severity), 0)


class OptimizationEngine:
    """Observe → analyze → plan → recommend → re-plan as conditions change."""

    def __init__(self) -> None:
        self.router = RoutingAgent()

    def replan(
        self,
        new_incident: IncidentResponse,
        incidents: list[IncidentResponse],
        resources: list[ResourceResponse],
        traffic: dict | None = None,
        baseline_eta: float | None = None,
    ) -> dict:
        if new_incident.severity != SeverityLevel.P1:
            return {"changed": False, "changes": [], "message": "No reallocation needed."}

        candidates = [
            item
            for item in resources
            if item.status == ResourceStatus.EN_ROUTE and item.current_incident_id
        ]
        if not candidates:
            return {"changed": False, "changes": [], "message": "No en-route units to reassign."}

        incident_lookup = {item.id: item for item in incidents}
        best = None
        best_gain = 0.0
        for resource in candidates:
            current = incident_lookup.get(resource.current_incident_id)
            if current and current.severity == SeverityLevel.P1:
                continue
            new_eta = self.router.eta_minutes(resource.location, new_incident.location, resource.speed_mph, traffic)
            old_eta = resource.eta or 8
            priority_bonus = 4 if current and current.severity in {SeverityLevel.P3, SeverityLevel.P4} else 1.5
            comparison_eta = baseline_eta if baseline_eta is not None else old_eta
            gain = comparison_eta - new_eta + priority_bonus
            if gain > best_gain:
                best = (resource, current, new_eta)
                best_gain = gain

        if not best:
            return {
                "changed": False,
                "changes": [],
                "message": "Current allocation remains optimal.",
            }

        resource, previous, new_eta = best
        previous_id = previous.id if previous else None
        return {
            "changed": True,
            "incident_id": new_incident.id,
            "message": (
                "Current resource allocation is no longer optimal. "
                f"Recalculating... Recommend diverting {resource.id.replace('_', ' ')} "
                f"to {new_incident.id}; dispatcher approval required."
            ),
            "changes": [
                {
                    "resource_id": resource.id,
                    "from_incident": previous_id,
                    "to_incident": new_incident.id,
                    "from_severity": get_severity_value(previous.severity) if previous else None,
                    "before_eta": baseline_eta,
                    "eta": new_eta,
                    "benefit_minutes": round(best_gain, 1),
                }
            ],
        }

    def _rank(self, severity: SeverityLevel | str) -> int:
        return severity_rank(severity)
