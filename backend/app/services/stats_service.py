from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from ..schemas.incident import IncidentResponse, SeverityLevel
from ..schemas.resource import ResourceResponse, ResourceType

class StatsService:
    @staticmethod
    def calculate_stats(
        incidents: List[IncidentResponse],
        resources: List[ResourceResponse],
        historical_data: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Calculate comprehensive statistics for the dashboard.

        Args:
            incidents: Current active incidents
            resources: Current resource states
            historical_data: Optional historical data for trends

        Returns:
            Dictionary of statistics
        """
        # Incident statistics
        incident_stats = StatsService._calculate_incident_stats(incidents)

        # Resource statistics
        resource_stats = StatsService._calculate_resource_stats(resources)

        # Response time statistics
        response_stats = StatsService._calculate_response_stats(incidents, resources)

        # Trend statistics (if historical data provided)
        trend_stats = {}
        if historical_data:
            trend_stats = StatsService._calculate_trends(historical_data)

        return {
            **incident_stats,
            **resource_stats,
            **response_stats,
            **trend_stats,
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def _calculate_incident_stats(incidents: List[IncidentResponse]) -> Dict:
        """Calculate incident-related statistics."""
        if not incidents:
            return {
                "total_incidents": 0,
                "by_severity": {s.value: 0 for s in SeverityLevel},
                "by_type": {},
                "pending_incidents": 0,
                "clustered_incidents": 0,
                "average_confidence": 0
            }

        # Count by severity
        by_severity = defaultdict(int)
        by_type = defaultdict(int)
        total_confidence = 0
        clustered_count = 0

        for incident in incidents:
            by_severity[incident.severity] += 1
            by_type[incident.incident_type.value] += 1
            total_confidence += incident.confidence

            if len(incident.clustered_calls) > 1:
                clustered_count += 1

        # Calculate averages
        avg_confidence = total_confidence / len(incidents)
        pending = sum(1 for i in incidents if i.status == "Pending")

        return {
            "total_incidents": len(incidents),
            "by_severity": dict(by_severity),
            "by_type": dict(by_type),
            "pending_incidents": pending,
            "clustered_incidents": clustered_count,
            "average_confidence": round(avg_confidence, 2),
            "critical_incidents": by_severity.get("P1", 0),
            "high_priority_incidents": by_severity.get("P1", 0) + by_severity.get("P2", 0)
        }

    @staticmethod
    def _calculate_resource_stats(resources: List[ResourceResponse]) -> Dict:
        """Calculate resource-related statistics."""
        if not resources:
            return {
                "total_resources": 0,
                "by_type": {rt.value: 0 for rt in ResourceType},
                "by_status": {},
                "utilization_rate": 0,
                "average_eta": 0
            }

        by_type = defaultdict(int)
        by_status = defaultdict(int)
        total_etas = []
        available_count = 0

        for resource in resources:
            by_type[resource.type.value] += 1
            by_status[resource.status.value] += 1

            if resource.status.value == "Available":
                available_count += 1

            if resource.eta is not None:
                total_etas.append(resource.eta)

        utilization_rate = 1 - (available_count / len(resources)) if resources else 0
        avg_eta = sum(total_etas) / len(total_etas) if total_etas else 0

        return {
            "total_resources": len(resources),
            "by_type": dict(by_type),
            "by_status": dict(by_status),
            "utilization_rate": round(utilization_rate, 2),
            "available_resources": available_count,
            "en_route_resources": by_status.get("En Route", 0),
            "on_scene_resources": by_status.get("On Scene", 0),
            "average_eta": round(avg_eta, 1) if avg_eta > 0 else 0
        }

    @staticmethod
    def _calculate_response_stats(
        incidents: List[IncidentResponse],
        resources: List[ResourceResponse]
    ) -> Dict:
        """Calculate response time statistics."""
        if not incidents or not resources:
            return {
                "average_response_time": 0,
                "response_times_by_severity": {},
                "unassigned_critical": 0,
                "longest_waiting": None
            }

        # Calculate response times for assigned incidents
        response_times = []
        by_severity = defaultdict(list)
        unassigned_critical = 0
        waiting_times = []

        for incident in incidents:
            if incident.assigned_resource:
                # Find the assigned resource
                resource = next(
                    (r for r in resources if r.id == incident.assigned_resource),
                    None
                )

                if resource and resource.eta is not None:
                    response_time = resource.eta
                    response_times.append(response_time)
                    by_severity[incident.severity].append(response_time)
            else:
                if incident.severity == "P1":
                    unassigned_critical += 1

                # Calculate waiting time
                call_time = datetime.fromisoformat(incident.timestamp)
                waiting_time = (datetime.now() - call_time).total_seconds() / 60
                waiting_times.append(waiting_time)

        avg_response = sum(response_times) / len(response_times) if response_times else 0
        longest_waiting = max(waiting_times) if waiting_times else 0

        # Format response times by severity
        response_by_severity = {
            s: round(sum(times)/len(times), 1) if times else 0
            for s, times in by_severity.items()
        }

        return {
            "average_response_time": round(avg_response, 1),
            "response_times_by_severity": response_by_severity,
            "unassigned_critical": unassigned_critical,
            "longest_waiting": round(longest_waiting, 1) if longest_waiting > 0 else 0,
            "median_response_time": StatsService._calculate_median(response_times)
        }

    @staticmethod
    def _calculate_trends(historical_data: List[Dict]) -> Dict:
        """Calculate trends from historical data."""
        if not historical_data:
            return {
                "hourly_trends": {},
                "daily_trends": {},
                "busy_hours": []
            }

        # Group by hour of day
        hourly = defaultdict(list)
        daily = defaultdict(list)

        for record in historical_data:
            try:
                dt = datetime.fromisoformat(record["timestamp"])
                hourly[dt.hour].append(record)
                daily[dt.date()].append(record)
            except (KeyError, ValueError):
                continue

        # Calculate hourly averages
        hourly_trends = {
            str(h): len(calls)
            for h, calls in hourly.items()
        }

        # Calculate daily averages
        daily_trends = {
            str(d): len(calls)
            for d, calls in daily.items()
        }

        # Find busy hours (top 3)
        busy_hours = sorted(
            hourly_trends.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]

        return {
            "hourly_trends": hourly_trends,
            "daily_trends": daily_trends,
            "busy_hours": [{"hour": h, "count": c} for h, c in busy_hours],
            "average_daily_calls": round(sum(len(v) for v in daily.values()) / len(daily), 1)
        }

    @staticmethod
    def _calculate_median(values: List[float]) -> float:
        """Calculate median of a list of values."""
        if not values:
            return 0

        sorted_values = sorted(values)
        n = len(sorted_values)

        if n % 2 == 1:
            return sorted_values[n//2]
        else:
            return (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2

    @staticmethod
    def generate_report(
        current_stats: Dict,
        historical_stats: Optional[Dict] = None
    ) -> Dict:
        """
        Generate a human-readable report from statistics.

        Args:
            current_stats: Current statistics
            historical_stats: Optional historical statistics for comparison

        Returns:
            Formatted report
        """
        report = {
            "summary": [],
            "warnings": [],
            "recommendations": []
        }

        # System status
        total_incidents = current_stats.get("total_incidents", 0)
        critical = current_stats.get("critical_incidents", 0)
        utilization = current_stats.get("utilization_rate", 0)

        report["summary"].append(
            f"System currently tracking {total_incidents} incidents "
            f"({critical} critical). Resource utilization at {utilization*100:.1f}%."
        )

        # Warnings
        if critical > 0:
            unassigned = current_stats.get("unassigned_critical", 0)
            if unassigned > 0:
                report["warnings"].append(
                    f"⚠️ {unassigned} critical incidents unassigned!"
                )

        if utilization > 0.8:
            report["warnings"].append(
                "⚠️ High resource utilization (>80%). Consider additional units."
            )

        # Recommendations
        avg_response = current_stats.get("average_response_time", 0)
        if avg_response > 10:  # More than 10 minutes
            report["recommendations"].append(
                "Consider reallocating resources to reduce response times."
            )

        if historical_stats:
            historical_avg = historical_stats.get("average_daily_calls", 0)
            current_daily = current_stats.get("total_incidents", 0)
            if current_daily > historical_avg * 1.5:
                report["recommendations"].append(
                    "Current call volume is 50% higher than average. "
                    "Monitor for potential surge."
                )

        return report