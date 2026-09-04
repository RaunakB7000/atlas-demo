from typing import Any, Optional

from pydantic import BaseModel, Field


class DashboardStats(BaseModel):
    total_incidents: int = 0
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_type: dict[str, int] = Field(default_factory=dict)
    pending_incidents: int = 0
    clustered_incidents: int = 0
    average_confidence: float = 0
    critical_incidents: int = 0
    high_priority_incidents: int = 0
    total_resources: int = 0
    by_resource_type: dict[str, int] = Field(default_factory=dict)
    by_status: dict[str, int] = Field(default_factory=dict)
    utilization_rate: float = 0
    available_resources: int = 0
    en_route_resources: int = 0
    on_scene_resources: int = 0
    average_eta: float = 0
    average_response_time: float = 0
    unassigned_critical: int = 0
    longest_waiting: float = 0
    incoming_reports: int = 0
    unique_incidents: int = 0
    timestamp: str = ""
    warnings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    extras: dict[str, Any] = Field(default_factory=dict)
    report: Optional[dict[str, Any]] = None
