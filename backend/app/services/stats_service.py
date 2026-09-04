from collections import defaultdict
from datetime import datetime
from typing import Any, Optional

from ..schemas.incident import IncidentResponse, SeverityLevel, get_severity_value
from ..schemas.resource import ResourceResponse, ResourceStatus, ResourceType

class StatsService:
    @staticmethod
    def calculate_stats(
        incidents: list[IncidentResponse],
        resources: list[ResourceResponse],
        incoming_reports: int = 0,
        historical_data: Optional[list[dict]] = None,
    ) -> dict[str, Any]:
        incident_stats = StatsService._calculate_incident_stats(incidents)
        resource_stats = StatsService._calculate_resource_stats(resources)
        response_stats = StatsService._calculate_response_stats(incidents, resources)
        trend_stats = StatsService._calculate_trends(historical_data or [])
        stats = {
            **incident_stats,
            **resource_stats,
            **response_stats,
            **trend_stats,
            "incoming_reports": incoming_reports,
            "unique_incidents": len(incidents),
            "timestamp": datetime.now().isoformat(),
        }
        stats["report"] = StatsService.generate_report(stats)
        stats["warnings"] = stats["report"]["warnings"]
        stats["recommendations"] = stats["report"]["recommendations"]
        return stats

    @staticmethod
    def _calculate_incident_stats(incidents: list[IncidentResponse]) -> dict[str, Any]:
        by_severity = {level.value: 0 for level in SeverityLevel}
        by_type: dict[str, int] = defaultdict(int)
        clustered = 0
        confidence_total = 0.0
        for incident in incidents:
            severity_str = get_severity_value(incident.severity)
            by_severity[severity_str] += 1
            by_type[str(incident.incident_type.value if hasattr(incident.incident_type, "value") else incident.incident_type)] += 1
            confidence_total += incident.confidence
            if incident.call_count > 1 or len(incident.clustered_calls) > 1:
                clustered += 1
        return {
            "total_incidents": len(incidents),
            "by_severity": by_severity,
            "by_type": dict(by_type),
            "pending_incidents": sum(1 for item in incidents if item.status == "Pending"),
            "clustered_incidents": clustered,
            "average_confidence": round(confidence_total / len(incidents), 2) if incidents else 0,
            "critical_incidents": by_severity.get("P1", 0),
            "high_priority_incidents": by_severity.get("P1", 0) + by_severity.get("P2", 0),
        }

    @staticmethod
    def _calculate_resource_stats(resources: list[ResourceResponse]) -> dict[str, Any]:
        by_type = {item.value: 0 for item in ResourceType}
        by_status = {item.value: 0 for item in ResourceStatus}
        etas = []
        for resource in resources:
            by_type[resource.type.value] += 1
            by_status[resource.status.value] += 1
            if resource.eta is not None:
                etas.append(resource.eta)
        available = by_status.get("Available", 0)
        return {
            "total_resources": len(resources),
            "by_resource_type": by_type,
            "by_status": by_status,
            "utilization_rate": round(1 - (available / len(resources)), 2) if resources else 0,
            "available_resources": available,
            "en_route_resources": by_status.get("En Route", 0),
            "on_scene_resources": by_status.get("On Scene", 0),
            "average_eta": round(sum(etas) / len(etas), 1) if etas else 0,
        }

    @staticmethod
    def _calculate_response_stats(
        incidents: list[IncidentResponse],
        resources: list[ResourceResponse],
    ) -> dict[str, Any]:
        response_times = []
        unassigned_critical = 0
        waiting = []
        for incident in incidents:
            if incident.assigned_resource:
                resource = next((item for item in resources if item.id == incident.assigned_resource), None)
                if resource and resource.eta is not None:
                    response_times.append(resource.eta)
            else:
                # Count unassigned P1 incidents correctly using consistent severity handling
                if get_severity_value(incident.severity) == "P1":
                    unassigned_critical += 1
                call_time = datetime.fromisoformat(incident.timestamp.replace("Z", "+00:00")).replace(tzinfo=None)
                waiting.append((datetime.now() - call_time).total_seconds() / 60)
        return {
            "average_response_time": round(sum(response_times) / len(response_times), 1) if response_times else 0,
            "unassigned_critical": unassigned_critical,
            "longest_waiting": round(max(waiting), 1) if waiting else 0,
        }

    @staticmethod
    def _calculate_trends(historical_data: list[dict]) -> dict[str, Any]:
        hourly: dict[str, int] = defaultdict(int)
        for record in historical_data:
            try:
                hourly[str(datetime.fromisoformat(record["timestamp"]).hour)] += 1
            except (KeyError, ValueError):
                continue
        busy = sorted(hourly.items(), key=lambda item: item[1], reverse=True)[:3]
        return {
            "hourly_trends": dict(hourly),
            "busy_hours": [{"hour": hour, "count": count} for hour, count in busy],
        }

    @staticmethod
    def generate_report(current_stats: dict[str, Any], historical_stats: Optional[dict] = None) -> dict[str, Any]:
        report = {"summary": [], "warnings": [], "recommendations": []}
        total = current_stats.get("total_incidents", 0)
        critical = current_stats.get("critical_incidents", 0)
        utilization = current_stats.get("utilization_rate", 0)
        report["summary"].append(
            f"Tracking {total} unique incidents ({critical} critical). "
            f"Resource utilization at {utilization * 100:.0f}%."
        )
        if current_stats.get("unassigned_critical", 0):
            report["warnings"].append(
                f"{current_stats['unassigned_critical']} critical incidents still unassigned."
            )
        if utilization > 0.8:
            report["warnings"].append("High resource utilization. Consider mutual aid.")
        if current_stats.get("average_response_time", 0) > 10:
            report["recommendations"].append("Reallocate units to cut response times.")
        return report
