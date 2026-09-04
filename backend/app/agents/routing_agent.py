from __future__ import annotations

from geopy.distance import geodesic

from ..schemas.incident import Location


class RoutingAgent:
    """Estimates travel time with simple traffic and closure penalties."""

    def eta_minutes(
        self,
        origin: Location | dict,
        destination: Location | dict,
        speed_mph: float,
        traffic: dict | None = None,
    ) -> float:
        origin_lat, origin_lng = self._coords(origin)
        dest_lat, dest_lng = self._coords(destination)
        distance_km = geodesic((origin_lat, origin_lng), (dest_lat, dest_lng)).km
        speed_kmh = max(speed_mph * 1.60934, 8)
        minutes = (distance_km / speed_kmh) * 60

        if traffic:
            for closure in traffic.get("road_closures", []):
                closure_loc = closure.get("location", {})
                if geodesic((dest_lat, dest_lng), (closure_loc.get("lat", 0), closure_loc.get("lng", 0))).km < 0.6:
                    minutes += 4
            for congestion in traffic.get("congestion_areas", []):
                minutes += congestion.get("delay_minutes", 0) * 0.15
        return round(minutes, 1)

    def _coords(self, point: Location | dict) -> tuple[float, float]:
        if isinstance(point, Location):
            return point.lat, point.lng
        return float(point["lat"]), float(point["lng"])
