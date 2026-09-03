from typing import List, Dict, Optional
from datetime import datetime
from ..schemas.incident import IncidentResponse, IncidentType, SeverityLevel
from ..schemas.resource import ResourceResponse
from ..agents.severity_classifier import SeverityClassifier
from ..agents.duplicate_detector import DuplicateDetector
from ..agents.incident_classifier import IncidentClassifier
from geopy.distance import geodesic

class CallProcessor:
    def __init__(self):
        self.severity_classifier = SeverityClassifier()
        self.incident_classifier = IncidentClassifier()
        self.duplicate_detector = DuplicateDetector()

    def process_call(self, call_data: Dict) -> IncidentResponse:
        """
        Process a single 911 call into a structured incident.

        Args:
            call_data: Raw call data from simulator

        Returns:
            Structured IncidentResponse
        """
        # Extract basic info
        transcript = call_data["transcript"]
        location = call_data["location"]
        timestamp = call_data.get("timestamp", datetime.now().isoformat())

        # Classify incident type and severity
        incident_type = self.incident_classifier.classify(transcript)
        severity = self.severity_classifier.classify(transcript, incident_type)

        # Create base incident
        incident = IncidentResponse(
            id=call_data["id"],
            transcript=transcript,
            incident_type=incident_type,
            severity=severity,
            location=location,
            timestamp=timestamp,
            confidence=0.9,  # Default confidence
            clustered_calls=[call_data["id"]],
            status="Pending"
        )

        # Add context based on incident type
        incident.context = self._generate_context(incident)

        return incident

    def process_batch(self, calls: List[Dict]) -> List[IncidentResponse]:
        """
        Process a batch of calls with duplicate detection.

        Args:
            calls: List of raw call data

        Returns:
            List of processed incidents (with duplicates merged)
        """
        # First pass: Process all calls individually
        incidents = [self.process_call(call) for call in calls]

        # Second pass: Detect and merge duplicates
        clusters = self.duplicate_detector.detect(incidents)

        # Create final incidents from clusters
        final_incidents = []
        for cluster_id, cluster_incidents in clusters.items():
            if len(cluster_incidents) == 1:
                final_incidents.append(cluster_incidents[0])
            else:
                final_incidents.append(self._merge_cluster(cluster_id, cluster_incidents))

        return final_incidents

    def _merge_cluster(self, cluster_id: int, incidents: List[IncidentResponse]) -> IncidentResponse:
        """
        Merge multiple incidents into a single cluster.

        Args:
            cluster_id: Unique cluster identifier
            incidents: List of incidents to merge

        Returns:
            Merged incident with combined data
        """
        # Use the most severe incident as base
        base_incident = max(incidents, key=lambda x: self._severity_rank(x.severity))

        # Combine all call IDs
        all_call_ids = []
        for incident in incidents:
            all_call_ids.extend(incident.clustered_calls)

        # Calculate average location (centroid)
        centroid = self._calculate_centroid([i.location for i in incidents])

        # Create merged incident
        merged = IncidentResponse(
            id=f"cluster_{cluster_id}",
            transcript=self._create_cluster_transcript(incidents),
            incident_type=base_incident.incident_type,
            severity=base_incident.severity,
            location=centroid,
            timestamp=min(i.timestamp for i in incidents),  # First call timestamp
            confidence=self._calculate_cluster_confidence(incidents),
            clustered_calls=list(set(all_call_ids)),  # Remove duplicates
            status="Clustered",
            context={
                "original_incidents": len(incidents),
                "call_ids": all_call_ids,
                "time_span": self._calculate_time_span(incidents)
            }
        )

        return merged

    def _severity_rank(self, severity: SeverityLevel) -> int:
        """Convert severity to numerical rank for comparison."""
        ranks = {"P1": 4, "P2": 3, "P3": 2, "P4": 1}
        return ranks.get(severity, 0)

    def _calculate_centroid(self, locations: List[Dict]) -> Dict:
        """Calculate geographic centroid of multiple locations."""
        if not locations:
            return {"lat": 0, "lng": 0}

        avg_lat = sum(loc["lat"] for loc in locations) / len(locations)
        avg_lng = sum(loc["lng"] for loc in locations) / len(locations)

        return {"lat": round(avg_lat, 6), "lng": round(avg_lng, 6)}

    def _create_cluster_transcript(self, incidents: List[IncidentResponse]) -> str:
        """Create a combined transcript for clustered incidents."""
        base = incidents[0].transcript
        others = [i.transcript for i in incidents[1:3]]  # Show first 2 additional calls

        summary = f"Multiple reports: {base}"
        if others:
            summary += f" | Similar reports: {'; '.join(others)}"

        if len(incidents) > 3:
            summary += f" | +{len(incidents)-3} more similar reports"

        return summary

    def _calculate_cluster_confidence(self, incidents: List[IncidentResponse]) -> float:
        """Calculate confidence score for the cluster."""
        # Base confidence on severity agreement
        severities = [i.severity for i in incidents]
        if len(set(severities)) == 1:
            confidence = 0.95
        else:
            confidence = 0.7

        # Adjust for geographic proximity
        locations = [i.location for i in incidents]
        max_dist = max(
            geodesic(
                (loc1["lat"], loc1["lng"]),
                (loc2["lat"], loc2["lng"])
            ).km
            for loc1 in locations
            for loc2 in locations
        )

        if max_dist < 0.5:  # Within 500m
            confidence *= 1.1
        elif max_dist > 2.0:  # More than 2km apart
            confidence *= 0.8

        return min(round(confidence, 2), 0.99)

    def _calculate_time_span(self, incidents: List[IncidentResponse]) -> str:
        """Calculate time span of all calls in the cluster."""
        timestamps = [datetime.fromisoformat(i.timestamp) for i in incidents]
        time_span = max(timestamps) - min(timestamps)

        if time_span.total_seconds() < 60:
            return f"{int(time_span.total_seconds())} seconds"
        elif time_span.total_seconds() < 3600:
            return f"{int(time_span.total_seconds()/60)} minutes"
        else:
            return f"{int(time_span.total_seconds()/3600)} hours"

    def _generate_context(self, incident: IncidentResponse) -> Dict:
        """Generate additional context based on incident details."""
        context = {
            "possible_conditions": [],
            "recommended_resources": []
        }

        # Medical incidents
        if incident.incident_type == IncidentType.MEDICAL:
            if "chest pain" in incident.transcript.lower():
                context["possible_conditions"].append("Possible cardiac event")
                context["recommended_resources"].append("ALS Ambulance")
            if "unconscious" in incident.transcript.lower():
                context["possible_conditions"].append("Possible unconsciousness")
                context["recommended_resources"].append("ALS Ambulance")

        # Fire incidents
        elif incident.incident_type == IncidentType.FIRE:
            if "apartment" in incident.transcript.lower():
                context["possible_conditions"].append("Structure fire")
                context["recommended_resources"].extend(["Fire Truck", "Ambulance"])

        # Accident incidents
        elif incident.incident_type == IncidentType.ACCIDENT:
            if "multi-vehicle" in incident.transcript.lower():
                context["possible_conditions"].append("Multi-vehicle collision")
                context["recommended_resources"].extend(["Fire Truck", "Ambulance", "Police"])

        return context