from typing import Any

from .air_client import air_client
from ..schemas.incident import IncidentType, SeverityLevel

P1_SIGNALS = [
    "cardiac",
    "unconscious",
    "not breathing",
    "not responding",
    "shots fired",
    "explosion",
    "collapsed",
    "structure fire",
    "apartment fire",
    "pedestrian struck",
]
P2_SIGNALS = [
    "chest pain",
    "stroke",
    "smoke",
    "multi-vehicle",
    "injuries",
    "weapon",
    "seizure",
]
P3_SIGNALS = ["accident", "collision", "fight", "gas leak", "suspicious"]


class SeverityAgent:
    """Recommends P1-P4 priority. Final dispatch stays with a human."""

    SYSTEM_PROMPT = (
        "You are Atlas Severity Agent. Classify the emergency as P1, P2, P3, or P4. "
        "P1 is immediate threat to life. Return JSON: severity, rationale, escalate."
    )

    def classify(self, transcript: str, incident_type: IncidentType) -> SeverityLevel:
        return self.recommend(transcript, incident_type)["severity"]

    def recommend(
        self,
        transcript: str,
        incident_type: IncidentType,
        deterministic: bool = False,
    ) -> dict[str, Any]:
        air_result = None
        if not deterministic:
            air_result = air_client.complete_json(
                self.SYSTEM_PROMPT,
                f"Type: {incident_type.value}\nTranscript: {transcript}",
            )
        if air_result and air_result.get("severity"):
            return {
                "severity": self._normalize(air_result.get("severity")),
                "rationale": air_result.get("rationale", "AIR severity recommendation"),
                "escalate": bool(air_result.get("escalate")),
                "source": "air",
            }
        result = self._heuristic(transcript, incident_type)
        if deterministic:
            result["source"] = "validated_scenario"
        return result

    def _heuristic(self, transcript: str, incident_type: IncidentType) -> dict[str, Any]:
        text = transcript.lower()
        if any(signal in text for signal in P1_SIGNALS):
            severity = SeverityLevel.P1
            rationale = "Immediate threat-to-life language detected."
        elif incident_type == IncidentType.FIRE and "apartment" in text:
            severity = SeverityLevel.P1
            rationale = "Possible occupied structure fire."
        elif any(signal in text for signal in P2_SIGNALS):
            severity = SeverityLevel.P2
            rationale = "Urgent medical or hazard indicators."
        elif any(signal in text for signal in P3_SIGNALS) or incident_type in {
            IncidentType.ACCIDENT,
            IncidentType.FIRE,
        }:
            severity = SeverityLevel.P3
            rationale = "Moderate incident requiring a response."
        else:
            severity = SeverityLevel.P4
            rationale = "No immediate life-threat markers."

        return {
            "severity": severity,
            "rationale": rationale,
            "escalate": severity == SeverityLevel.P1,
            "source": "local",
        }

    def _normalize(self, value: Any) -> SeverityLevel:
        text = str(value or "P3").upper()
        try:
            return SeverityLevel(text)
        except ValueError:
            return SeverityLevel.P3
