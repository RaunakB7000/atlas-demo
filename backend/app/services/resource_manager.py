from typing import List, Dict, Optional
from ..schemas.incident import IncidentResponse
from ..schemas.resource import ResourceResponse, ResourceType, ResourceStatus
from geopy.distance import geodesic
from datetime import datetime, timedelta
import heapq

class ResourceManager:
    def __init__(self, initial_resources: List[ResourceResponse]):
        self.resources = {r.id: r for r in initial_resources}
        self.resource_types = {
            ResourceType.AMBULANCE: [],
            ResourceType.FIRE_TRUCK: [],
            ResourceType.POLICE: [],
            ResourceType.AIR_AMBULANCE: []
        }
        self._initialize_resource_pools()

    def _initialize_resource_pools(self):
        """Initialize resource pools by type."""
        for resource in self.resources.values():
            self.resource_types[resource.type].append(resource.id)

    def allocate_resources(self, incidents: List[IncidentResponse]) -> List[ResourceResponse]:
        """
        Allocate resources to incidents using a priority-based algorithm.

        Args:
            incidents: List of incidents needing resources

        Returns:
            List of updated resources
        """
        # Sort incidents by priority (P1 first, then by time)
        sorted_incidents = sorted(
            incidents,
            key=lambda x: (self._severity_priority(x.severity), x.timestamp)
        )

        for incident in sorted_incidents:
            if incident.assigned_resource:
                continue  # Already assigned

            required_types = self._get_required_resources(incident)
            assigned = False

            for resource_type in required_types:
                available = self._get_available_resources(resource_type)

                if not available:
                    continue

                # Find closest available resource
                closest = self._find_closest_resource(incident, available)

                if closest:
                    self._assign_resource(closest, incident)
                    assigned = True
                    break

            if not assigned and incident.severity == SeverityLevel.P1:
                # For P1 incidents, try any available resource
                for resource_type in ResourceType:
                    available = self._get_available_resources(resource_type)
                    if available:
                        closest = self._find_closest_resource(incident, available)
                        if closest:
                            self._assign_resource(closest, incident)
                            break

        return list(self.resources.values())

    def _severity_priority(self, severity: str) -> int:
        """Convert severity to numerical priority (lower is higher priority)."""
        priorities = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}
        return priorities.get(severity, 4)

    def _get_required_resources(self, incident: IncidentResponse) -> List[ResourceType]:
        """Determine what resource types are needed for an incident."""
        required = []

        # All incidents need at least one resource
        if incident.incident_type == IncidentType.MEDICAL:
            required.append(ResourceType.AMBULANCE)
            if "cardiac" in incident.transcript.lower() or "unconscious" in incident.transcript.lower():
                # Critical medical needs fastest response
                required.insert(0, ResourceType.AIR_AMBULANCE)

        elif incident.incident_type == IncidentType.FIRE:
            required.append(ResourceType.FIRE_TRUCK)
            required.append(ResourceType.AMBULANCE)  # Always send medical with fire

        elif incident.incident_type == IncidentType.ACCIDENT:
            required.append(ResourceType.POLICE)
            if "multi-vehicle" in incident.transcript.lower() or "injuries" in incident.transcript.lower():
                required.append(ResourceType.AMBULANCE)
                required.append(ResourceType.FIRE_TRUCK)

        elif incident.incident_type == IncidentType.DISTURBANCE:
            required.append(ResourceType.POLICE)

        return required

    def _get_available_resources(self, resource_type: ResourceType) -> List[ResourceResponse]:
        """Get all available resources of a specific type."""
        return [
            self.resources[rid]
            for rid in self.resource_types[resource_type]
            if self.resources[rid].status == ResourceStatus.AVAILABLE
        ]

    def _find_closest_resource(self, incident: IncidentResponse, resources: List[ResourceResponse]) -> Optional[ResourceResponse]:
        """Find the closest available resource to an incident."""
        if not resources:
            return None

        incident_loc = (incident.location.lat, incident.location.lng)
        resource_distances = []

        for resource in resources:
            resource_loc = (resource.location.lat, resource.location.lng)
            distance = geodesic(incident_loc, resource_loc).km
            resource_distances.append((distance, resource))

        # Return the closest resource
        return min(resource_distances, key=lambda x: x[0])[1]

    def _assign_resource(self, resource: ResourceResponse, incident: IncidentResponse):
        """Assign a resource to an incident and update status."""
        resource.status = ResourceStatus.EN_ROUTE
        resource.current_incident_id = incident.id

        # Calculate ETA (simplified)
        incident_loc = (incident.location.lat, incident.location.lng)
        resource_loc = (resource.location.lat, resource.location.lng)
        distance_km = geodesic(incident_loc, resource_loc).km
        resource.eta = distance_km / (resource.speed_mph * 1.60934) * 60  # Convert to minutes

        # Update incident
        incident.assigned_resource = resource.id

    def update_resource_status(self):
        """Update resource statuses (e.g., arrived on scene)."""
        for resource in self.resources.values():
            if resource.status == ResourceStatus.EN_ROUTE and resource.eta is not None:
                # Simulate movement (reduce ETA)
                resource.eta = max(0, resource.eta - 0.5)  # Reduce by 30 seconds

                if resource.eta <= 0:
                    resource.status = ResourceStatus.ON_SCENE

    def release_resource(self, resource_id: str):
        """Release a resource back to available pool."""
        if resource_id in self.resources:
            resource = self.resources[resource_id]
            resource.status = ResourceStatus.AVAILABLE
            resource.current_incident_id = None
            resource.eta = None

            # Return to station (simplified - just reset to original station location)
            # In a real implementation, you'd track the station location
            if "Station" in resource.station:
                resource.location = {
                    "lat": 33.4186 if "Fire" in resource.station else 33.4255,
                    "lng": -111.9332 if "Fire" in resource.station else -111.9400
                }

    def get_resource_utilization(self) -> Dict:
        """Get current resource utilization statistics."""
        total = {rt: len(ids) for rt, ids in self.resource_types.items()}
        available = {
            rt: len([rid for rid in ids if self.resources[rid].status == ResourceStatus.AVAILABLE])
            for rt, ids in self.resource_types.items()
        }
        en_route = {
            rt: len([rid for rid in ids if self.resources[rid].status == ResourceStatus.EN_ROUTE])
            for rt, ids in self.resource_types.items()
        }
        on_scene = {
            rt: len([rid for rid in ids if self.resources[rid].status == ResourceStatus.ON_SCENE])
            for rt, ids in self.resource_types.items()
        }

        return {
            "total": total,
            "available": available,
            "en_route": en_route,
            "on_scene": on_scene,
            "utilization": {
                rt: 1 - (available[rt] / total[rt]) if total[rt] > 0 else 0
                for rt in ResourceType
            }
        }

    def reallocate_resources(self, new_incident: IncidentResponse):
        """
        Reallocate resources when a new high-priority incident arrives.
        May reassign resources from lower-priority incidents.
        """
        if new_incident.severity != SeverityLevel.P1:
            return  # Only reallocate for P1 incidents

        # Find all currently assigned resources
        assigned_resources = [
            r for r in self.resources.values()
            if r.status == ResourceStatus.EN_ROUTE and r.current_incident_id
        ]

        # Get the incident this would be reassigned from
        original_incident_id = assigned_resources[0].current_incident_id

        # Find the original incident
        # (In a real implementation, you'd have access to all incidents)
        original_incident = None  # Would be retrieved from your incident store

        # Only reassign if the new incident is higher priority
        if original_incident and self._severity_priority(new_incident.severity) < self._severity_priority(original_incident.severity):
            # Reassign the closest resource
            closest = self._find_closest_resource(new_incident, assigned_resources)
            if closest:
                # Release from original incident
                if original_incident:
                    original_incident.assigned_resource = None
                    original_incident.status = "Pending"

                # Assign to new incident
                self._assign_resource(closest, new_incident)

                return True

        return False