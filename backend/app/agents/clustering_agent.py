from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Iterable

from geopy.distance import geodesic

from .air_client import air_client
from ..schemas.incident import IncidentResponse


def _cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


class ClusteringAgent:
    """Merges duplicate 911 reports using geography, time, and embeddings."""

    def __init__(
        self,
        max_km: float = 0.9,
        max_minutes: float = 20,
        min_similarity: float = 0.42,
    ) -> None:
        self.max_km = max_km
        self.max_minutes = max_minutes
        self.min_similarity = min_similarity

    def detect(self, incidents: list[IncidentResponse]) -> dict[int, list[IncidentResponse]]:
        if not incidents:
            return {}

        embeddings = air_client.embed(
            [f"{item.incident_type.value} {item.transcript}" for item in incidents]
        )
        parent = list(range(len(incidents)))

        def find(index: int) -> int:
            while parent[index] != index:
                parent[index] = parent[parent[index]]
                index = parent[index]
            return index

        for i, left in enumerate(incidents):
            for j, right in enumerate(incidents[i + 1 :], start=i + 1):
                if self._same_event(left, right, embeddings[i], embeddings[j]):
                    parent[find(j)] = find(i)

        clusters: dict[int, list[IncidentResponse]] = defaultdict(list)
        for index, incident in enumerate(incidents):
            clusters[find(index)].append(incident)
        return dict(clusters)

    def find_match(
        self,
        incoming: IncidentResponse,
        existing: Iterable[IncidentResponse],
    ) -> IncidentResponse | None:
        existing_list = list(existing)
        if not existing_list:
            return None
        embeddings = air_client.embed(
            [f"{incoming.incident_type.value} {incoming.transcript}"]
            + [f"{item.incident_type.value} {item.transcript}" for item in existing_list]
        )
        incoming_vec = embeddings[0]
        best = None
        best_score = 0.0
        for item, vector in zip(existing_list, embeddings[1:]):
            if not self._same_event(incoming, item, incoming_vec, vector):
                continue
            score = _cosine(incoming_vec, vector)
            if score > best_score:
                best = item
                best_score = score
        return best

    def _same_event(
        self,
        left: IncidentResponse,
        right: IncidentResponse,
        left_vec: list[float],
        right_vec: list[float],
    ) -> bool:
        if left.incident_type != right.incident_type:
            return False
        distance = geodesic(
            (left.location.lat, left.location.lng),
            (right.location.lat, right.location.lng),
        ).km
        minutes = abs(self._parse(left.timestamp) - self._parse(right.timestamp)).total_seconds() / 60
        similarity = _cosine(left_vec, right_vec)
        return distance <= self.max_km and minutes <= self.max_minutes and similarity >= self.min_similarity

    def _parse(self, value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
