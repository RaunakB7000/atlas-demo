from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any

from fastapi import WebSocket
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database.seed import clear_operational_data, seed_operational_data
from ..database.session import SessionLocal
from ..models.call import Call
from ..models.hospital import Hospital
from ..models.incident import Incident
from ..models.prediction import Prediction
from ..models.resource import Resource
from ..schemas.incident import IncidentResponse, Location, SeverityLevel, get_severity_value
from ..schemas.resource import HospitalResponse, ResourceResponse, ResourceStatus, ResourceType
from ..simulator.call_streamer import (
    DEFAULT_SCENARIO,
    SCENARIOS,
    generate_critical_inject,
    generate_historical_data,
    seed_simulation,
    stream_calls,
)
from ..simulator.resource_simulator import generate_traffic_conditions
from .call_processor import CallProcessor, incident_to_record, record_to_incident
from .optimization_engine import OptimizationEngine
from .resource_manager import ResourceManager
from .stats_service import StatsService


class SimulationEngine:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.processor = CallProcessor()
        self.manager = ResourceManager()
        self.optimizer = OptimizationEngine()
        self.subscribers: list[WebSocket] = []
        self.state = "idle"
        self.incoming_reports = 0
        self.next_call_id = 1
        self.task: asyncio.Task | None = None
        self.lifecycle_task: asyncio.Task | None = None
        self._on_scene_ticks: dict[str, int] = {}
        self.traffic = generate_traffic_conditions()
        self.historical = generate_historical_data()
        self.last_event: str | None = None
        self.target_calls = self.settings.SIMULATION_CALL_COUNT
        self.scenario = DEFAULT_SCENARIO
        self.timeline: list[dict[str, Any]] = []
        self._event_counter = 0
        self.started_at: datetime | None = None
        self.completed_at: datetime | None = None
        self.peak_utilization = 0.0
        self._lock = asyncio.Lock()

    async def subscribe(self, websocket: WebSocket) -> None:
        self.subscribers.append(websocket)
        await self._send(websocket, {"type": "snapshot", "data": self.snapshot()})

    def unsubscribe(self, websocket: WebSocket) -> None:
        if websocket in self.subscribers:
            self.subscribers.remove(websocket)

    def snapshot(self) -> dict[str, Any]:
        db = SessionLocal()
        try:
            incidents = [record_to_incident(row) for row in db.query(Incident).all()]
            resources = [self._resource_schema(row) for row in db.query(Resource).all()]
            hospitals = [self._hospital_schema(row) for row in db.query(Hospital).all()]
            predictions = [
                {
                    "id": row.id,
                    "label": row.label,
                    "lat": row.lat,
                    "lng": row.lng,
                    "hour": row.hour,
                    "probability": row.probability,
                    "recommendation": row.recommendation,
                }
                for row in db.query(Prediction).all()
            ]
            stats = StatsService.calculate_stats(incidents, resources, self.incoming_reports, self.historical)
            self.peak_utilization = max(self.peak_utilization, stats.get("utilization_rate", 0))
            return {
                "status": self.status_payload(),
                "incidents": [item.model_dump() for item in incidents],
                "resources": [item.model_dump() for item in resources],
                "hospitals": [item.model_dump() for item in hospitals],
                "predictions": predictions,
                "stats": stats,
                "traffic": self.traffic,
                "timeline": list(self.timeline),
                "after_action_report": self._after_action_report(stats, incidents),
                "scenario": self._scenario_payload(),
            }
        finally:
            db.close()

    def status_payload(self) -> dict[str, Any]:
        db = SessionLocal()
        try:
            incidents = db.query(Incident).all()
            by_severity = {"P1": 0, "P2": 0, "P3": 0, "P4": 0}
            for row in incidents:
                severity_str = get_severity_value(row.severity)
                by_severity[severity_str] = by_severity.get(severity_str, 0) + 1
            return {
                "state": self.state,
                "incoming_reports": self.incoming_reports,
                "transcribed": self.incoming_reports,
                "unique_incidents": len(incidents),
                "critical": by_severity["P1"],
                "high_priority": by_severity["P2"],
                "medium": by_severity["P3"],
                "low": by_severity["P4"],
                "target_calls": self.target_calls,
                "last_event": self.last_event,
                "scenario": self.scenario,
                "scenario_label": SCENARIOS[self.scenario]["label"],
                "started_at": self.started_at.isoformat() if self.started_at else None,
            }
        finally:
            db.close()

    async def start(
        self,
        num_calls: int | None = None,
        delay: float | None = None,
        scenario: str | None = None,
    ) -> dict[str, Any]:
        if self.state == "running":
            return self.status_payload()
        delay = self.settings.SIMULATION_DELAY_SECONDS if delay is None else delay
        await self._cancel_background_tasks()

        if self.state == "paused" and self.incoming_reports < self.target_calls:
            self.state = "running"
            remaining = self.target_calls - self.incoming_reports
            self.last_event = "Simulation resumed."
            self._record_event("system", "Simulation resumed", f"{remaining} reports remain in the scenario.")
            self.task = asyncio.create_task(self._run_loop(remaining, delay))
            await self.broadcast({"type": "status", "data": self.status_payload()})
            await self.broadcast({"type": "timeline", "data": list(self.timeline)})
            return self.status_payload()

        self.scenario = scenario if scenario in SCENARIOS else DEFAULT_SCENARIO
        scenario_config = SCENARIOS[self.scenario]
        self.target_calls = num_calls if num_calls is not None else scenario_config["default_calls"]
        async with self._lock:
            seed_simulation(scenario_config["seed"])
            self._reset_db()
            self._on_scene_ticks.clear()
            self.incoming_reports = 0
            self.next_call_id = 1
            self.state = "running"
            self.timeline.clear()
            self._event_counter = 0
            self.started_at = datetime.now()
            self.completed_at = None
            self.peak_utilization = 0.0
            self.last_event = "Emergency simulation started."
            self._record_event(
                "system",
                f"{scenario_config['label']} started",
                f"Monitoring {self.target_calls} deterministic synthetic reports.",
                {"scenario": self.scenario},
            )
        self.task = asyncio.create_task(self._run_loop(self.target_calls, delay))
        await self.broadcast({"type": "snapshot", "data": self.snapshot()})
        await self.broadcast({"type": "status", "data": self.status_payload()})
        return self.status_payload()

    async def pause(self) -> dict[str, Any]:
        self.state = "paused"
        self.last_event = "Simulation paused."
        await self._cancel_background_tasks()
        self._record_event("system", "Simulation paused", "The current operational state has been preserved.")
        await self.broadcast({"type": "status", "data": self.status_payload()})
        await self.broadcast({"type": "timeline", "data": list(self.timeline)})
        return self.status_payload()

    async def reset(self) -> dict[str, Any]:
        self.state = "idle"
        await self._cancel_background_tasks()
        async with self._lock:
            self.incoming_reports = 0
            self.next_call_id = 1
            self._on_scene_ticks.clear()
            self.last_event = "Simulation reset."
            self.timeline.clear()
            self._event_counter = 0
            self.started_at = None
            self.completed_at = None
            self.peak_utilization = 0.0
            self._reset_db()
        await self.broadcast({"type": "snapshot", "data": self.snapshot()})
        return self.status_payload()

    async def inject_critical(self) -> dict[str, Any]:
        async with self._lock:
            call = generate_critical_inject(
                self._allocate_call_id(offset=100000), scenario=self.scenario
            )
            self._record_event(
                "warning",
                "Critical incident received",
                "Multi-vehicle collision with trapped occupants reported near Rural and Broadway.",
            )
            await self.broadcast(
                {
                    "type": "alert",
                    "data": {
                        "title": "NEW INCIDENT",
                        "message": "Major collision reported. Current resource allocation is no longer optimal. Recalculating...",
                    },
                }
            )
            result = await self._ingest_calls([call], allow_replan=True)
            self.last_event = result.get("reallocation", {}).get("message") or "Critical incident injected."
            await self.broadcast({"type": "timeline", "data": list(self.timeline)})
            return result

    async def approve_incident(self, incident_id: str) -> dict[str, Any]:
        changed_incidents: list[IncidentResponse] = []
        async with self._lock:
            db = SessionLocal()
            try:
                row = db.query(Incident).filter(Incident.id == incident_id).first()
                if not row:
                    return {"message": "Incident not found"}

                incident = record_to_incident(row)
                if incident.status == "Resolved":
                    return incident.model_dump()

                resources = [self._resource_schema(item) for item in db.query(Resource).all()]
                hospitals = [
                    {
                        "id": item.id,
                        "name": item.name,
                        "lat": item.lat,
                        "lng": item.lng,
                        "capacity": item.capacity,
                        "occupancy": item.occupancy,
                    }
                    for item in db.query(Hospital).all()
                ]
                self.manager.load(resources)

                if incident.assigned_resource:
                    assigned = self.manager.resources.get(incident.assigned_resource)
                    if assigned and assigned.current_incident_id == incident.id:
                        incident.dispatcher_approved = True
                        self._upsert_incident(db, incident)
                        db.commit()
                        changed_incidents.append(incident)
                    else:
                        incident.assigned_resource = None

                if not incident.assigned_resource:
                    candidate_id = incident.context.get("recommended_resource_id")
                    candidate = self.manager.resources.get(candidate_id) if candidate_id else None
                    diversion_from = incident.context.get("replan_from_incident")

                    if not candidate or (
                        candidate.status != ResourceStatus.AVAILABLE
                        and not (
                            diversion_from
                            and candidate.current_incident_id == diversion_from
                            and candidate.status == ResourceStatus.EN_ROUTE
                        )
                    ):
                        recommendation = self.manager.recommend_only(
                            incident, hospitals, self.traffic
                        )
                        candidate_id = recommendation.get("primary_resource_id")
                        candidate = self.manager.resources.get(candidate_id) if candidate_id else None
                        diversion_from = None
                        self.manager.apply_recommendation(incident, recommendation)

                    if not candidate_id and get_severity_value(incident.severity) == "P1":
                        proposal = self.optimizer.replan(
                            incident,
                            [record_to_incident(item) for item in db.query(Incident).all()],
                            list(self.manager.resources.values()),
                            self.traffic,
                        )
                        if proposal["changed"]:
                            change = proposal["changes"][0]
                            candidate_id = change["resource_id"]
                            diversion_from = change["from_incident"]
                            candidate = self.manager.resources[candidate_id]
                            incident.context = {
                                **incident.context,
                                "recommended_resource_id": candidate_id,
                                "replan_from_incident": diversion_from,
                            }
                            incident.recommended_response = (
                                f"Divert {candidate_id.replace('_', ' ')}"
                            )

                    if candidate and diversion_from:
                        previous_row = db.query(Incident).filter(
                            Incident.id == diversion_from
                        ).first()
                        if previous_row:
                            previous = record_to_incident(previous_row)
                            previous.assigned_resource = None
                            previous.dispatcher_approved = False
                            previous.status = "Recommended"
                            previous.context = {
                                **previous.context,
                                "diverted_resource_id": candidate.id,
                            }
                            self._upsert_incident(db, previous)
                            changed_incidents.append(previous)
                        candidate.status = ResourceStatus.AVAILABLE
                        candidate.current_incident_id = None
                        candidate.eta = None

                    dispatched = (
                        self.manager.dispatch_resource(candidate_id, incident, self.traffic)
                        if candidate_id
                        else None
                    )
                    if dispatched:
                        incident.dispatcher_approved = True
                        incident.context = {
                            **incident.context,
                            "recommended_resource_id": dispatched.id,
                        }
                        self._upsert_resource(db, dispatched)
                    else:
                        incident.dispatcher_approved = False
                        incident.status = "Awaiting Resource"
                        incident.recommended_response = "No unit currently available"

                    self._upsert_incident(db, incident)
                    db.commit()
                    changed_incidents.append(incident)
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()

        snapshot = self.snapshot()
        approved = changed_incidents[-1] if changed_incidents else None
        if approved and approved.dispatcher_approved:
            if approved.context.get("replan_from_incident"):
                self._record_event(
                    "replan",
                    "Re-plan approved",
                    f"{approved.assigned_resource.replace('_', ' ')} diverted to {approved.id}.",
                    approved.context.get("replan", {}),
                )
            self._record_event(
                "dispatch",
                "Recommendation approved",
                f"{approved.assigned_resource.replace('_', ' ')} dispatched to {approved.id}.",
                {"incident_id": approved.id, "resource_id": approved.assigned_resource},
            )
        for changed in changed_incidents:
            await self.broadcast({"type": "incident", "data": changed.model_dump()})
        await self.broadcast({"type": "resources", "data": snapshot["resources"]})
        await self.broadcast({"type": "stats", "data": snapshot["stats"]})
        await self.broadcast({"type": "status", "data": snapshot["status"]})
        await self.broadcast({"type": "timeline", "data": list(self.timeline)})

        if self.state != "running" and any(
            item["status"] in {ResourceStatus.EN_ROUTE.value, ResourceStatus.ON_SCENE.value}
            for item in snapshot["resources"]
        ):
            self._ensure_lifecycle_task()
        return changed_incidents[-1].model_dump()

    async def broadcast(self, message: dict[str, Any]) -> None:
        stale = []
        for socket in self.subscribers:
            try:
                await socket.send_json(message)
            except Exception:
                stale.append(socket)
        for socket in stale:
            self.unsubscribe(socket)

    async def _run_loop(self, remaining: int, delay: float) -> None:
        try:
            async for batch in stream_calls(
                num_calls=remaining,
                delay=0,
                batch_size=self.settings.SIMULATION_BATCH_SIZE,
                start_id=self.next_call_id,
                scenario=self.scenario,
                seed=SCENARIOS[self.scenario]["seed"] if self.incoming_reports == 0 else None,
            ):
                if self.state != "running":
                    break
                async with self._lock:
                    self.next_call_id = max(self.next_call_id, batch[-1]["id"] + 1)
                    await self._ingest_calls(batch, allow_replan=False)
                    await self._tick_resources()
                await asyncio.sleep(delay)
            if self.state == "running":
                for _ in range(500):
                    async with self._lock:
                        active = await self._tick_resources()
                    if not active or self.state != "running":
                        break
                    await asyncio.sleep(max(delay, 0))
                if self.state == "running":
                    self.state = "complete"
                    self.completed_at = datetime.now()
                    self.last_event = "Simulation complete."
                    self._record_event(
                        "system",
                        "Scenario processing complete",
                        f"All {self.incoming_reports} reports have been analyzed.",
                    )
                    await self.broadcast({"type": "status", "data": self.status_payload()})
                    await self.broadcast({"type": "timeline", "data": list(self.timeline)})
        except asyncio.CancelledError:
            return
        except Exception as exc:
            self.state = "error"
            self.last_event = f"Simulation error: {exc}"
            await self.broadcast({"type": "status", "data": self.status_payload()})

    async def _ingest_calls(self, calls: list[dict[str, Any]], allow_replan: bool) -> dict[str, Any]:
        db = SessionLocal()
        reallocation = {"changed": False, "changes": [], "message": ""}
        call_events: list[dict[str, Any]] = []
        try:
            existing = [record_to_incident(row) for row in db.query(Incident).all()]
            resources = [self._resource_schema(row) for row in db.query(Resource).all()]
            hospitals = [
                {"id": row.id, "name": row.name, "lat": row.lat, "lng": row.lng, "capacity": row.capacity, "occupancy": row.occupancy}
                for row in db.query(Hospital).all()
            ]
            self.manager.load(resources)
            processed: list[IncidentResponse] = []
            merged_count = 0

            for call in calls:
                self.incoming_reports += 1
                db.merge(
                    Call(
                        id=call["id"],
                        transcript=call["transcript"],
                        lat=call["location"]["lat"],
                        lng=call["location"]["lng"],
                        timestamp=datetime.fromisoformat(call["timestamp"]),
                        incident_type=call.get("incident_type"),
                        raw_audio_url=call.get("raw_audio_url"),
                        processed=True,
                        context=json.dumps(call.get("context", {})),
                    )
                )
                incoming = self.processor.process_call(call)
                match = self.processor.clustering.find_match(incoming, existing)
                if match:
                    merged_count += 1
                    merged = self.processor.merge_into(match, incoming)
                    existing = [merged if item.id == match.id else item for item in existing]
                    processed.append(merged)
                    call_events.append({**call, "merged_into": match.id})
                else:
                    existing.append(incoming)
                    processed.append(incoming)
                    call_events.append(call)

            unassigned = [
                item
                for item in existing
                if not item.assigned_resource and item.status != "Resolved"
            ]
            self.manager.allocate_resources(unassigned, hospitals, self.traffic)

            self._record_event(
                "ingest",
                f"{len(calls)} report{'s' if len(calls) != 1 else ''} analyzed",
                (
                    f"{merged_count} duplicate report{'s' if merged_count != 1 else ''} consolidated; "
                    f"{len(calls) - merged_count} incident update{'s' if len(calls) - merged_count != 1 else ''} created."
                ),
                {"reports": len(calls), "duplicates": merged_count},
            )

            if allow_replan:
                critical = next((item for item in processed if get_severity_value(item.severity) == "P1"), processed[-1] if processed else None)
                if critical:
                    explanation = critical.context.get("recommendation_explanation", {})
                    before_resource = critical.context.get("recommended_resource_id")
                    before_eta = explanation.get("selected_eta")
                    reallocation = self.optimizer.replan(
                        critical,
                        existing,
                        list(self.manager.resources.values()),
                        self.traffic,
                        baseline_eta=before_eta,
                    )
                    if reallocation["changed"]:
                        change = reallocation["changes"][0]
                        critical.context = {
                            **critical.context,
                            "recommended_resource_id": change["resource_id"],
                            "replan_from_incident": change["from_incident"],
                            "replan": {
                                "before_resource_id": before_resource,
                                "before_eta": before_eta,
                                "after_resource_id": change["resource_id"],
                                "after_eta": change["eta"],
                                "from_incident": change["from_incident"],
                                "to_incident": critical.id,
                                "benefit_minutes": change.get("benefit_minutes"),
                            },
                        }
                        critical.recommended_response = (
                            f"Divert {change['resource_id'].replace('_', ' ')}"
                        )
                        critical.status = "Recommended"
                        self._record_event(
                            "replan",
                            "Resource plan updated",
                            reallocation["message"],
                            critical.context["replan"],
                        )

            for incident in existing:
                self._upsert_incident(db, incident)
            for resource in self.manager.resources.values():
                self._upsert_resource(db, resource)
            db.commit()

            snapshot = self.snapshot()
            for event in call_events:
                await self.broadcast({"type": "call", "data": event})
            for incident in processed:
                await self.broadcast({"type": "incident", "data": incident.model_dump()})
            if reallocation["changed"]:
                await self.broadcast({"type": "reallocation", "data": reallocation})
            await self.broadcast({"type": "resources", "data": snapshot["resources"]})
            await self.broadcast({"type": "stats", "data": snapshot["stats"]})
            await self.broadcast({"type": "status", "data": snapshot["status"]})
            return {"incidents": [item.model_dump() for item in processed], "reallocation": reallocation}
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def _allocate_call_id(self, offset: int = 0) -> int:
        db = SessionLocal()
        try:
            max_id = db.query(func.max(Call.id)).scalar() or 0
        finally:
            db.close()
        self.next_call_id = max(self.next_call_id, max_id + 1, offset)
        allocated = self.next_call_id
        self.next_call_id += 1
        return allocated

    async def _tick_resources(self) -> bool:
        db = SessionLocal()
        changed_incident_ids: set[str] = set()
        timeline_changed = False
        try:
            resources = [self._resource_schema(row) for row in db.query(Resource).all()]
            incidents = {row.id: row for row in db.query(Incident).all()}
            self.manager.load(resources)

            for resource in self.manager.resources.values():
                if resource.status == ResourceStatus.EN_ROUTE and resource.current_incident_id in incidents:
                    target = incidents[resource.current_incident_id]
                    lat_diff = target.lat - resource.location.lat
                    lng_diff = target.lng - resource.location.lng

                    resource.location = Location(
                        lat=round(resource.location.lat + lat_diff * 0.35, 6),
                        lng=round(resource.location.lng + lng_diff * 0.35, 6),
                    )
                    resource.eta = max(0, round((resource.eta or 0) - 0.4, 1))
                    arrived = (
                        resource.eta <= 0
                        or (abs(lat_diff) < 0.002 and abs(lng_diff) < 0.002)
                    )
                    if arrived:
                        resource.location = Location(lat=target.lat, lng=target.lng)
                        resource.status = ResourceStatus.ON_SCENE
                        resource.eta = 0
                        target.status = "On Scene"
                        self._on_scene_ticks.setdefault(
                            resource.id,
                            max(1, self.settings.SIMULATION_ON_SCENE_TICKS),
                        )
                        self._record_event(
                            "arrival",
                            "Unit arrived on scene",
                            f"{resource.id.replace('_', ' ')} arrived at {target.id}.",
                            {"incident_id": target.id, "resource_id": resource.id},
                        )
                        timeline_changed = True
                    else:
                        target.status = "En Route"
                    changed_incident_ids.add(target.id)
                elif resource.status == ResourceStatus.EN_ROUTE:
                    self.manager.release_resource(resource.id)
                    self._on_scene_ticks.pop(resource.id, None)
                elif resource.status == ResourceStatus.ON_SCENE:
                    target = incidents.get(resource.current_incident_id or "")
                    remaining = self._on_scene_ticks.get(
                        resource.id,
                        max(1, self.settings.SIMULATION_ON_SCENE_TICKS),
                    ) - 1
                    if remaining <= 0:
                        if target:
                            target.status = "Resolved"
                            changed_incident_ids.add(target.id)
                            self._record_event(
                                "resolution",
                                "Incident resolved",
                                f"{target.id} cleared; {resource.id.replace('_', ' ')} returned to service.",
                                {"incident_id": target.id, "resource_id": resource.id},
                            )
                            timeline_changed = True
                        self.manager.release_resource(resource.id)
                        self._on_scene_ticks.pop(resource.id, None)
                    else:
                        self._on_scene_ticks[resource.id] = remaining
                else:
                    self._on_scene_ticks.pop(resource.id, None)

                self._upsert_resource(db, resource)
            db.commit()
            for incident_id in changed_incident_ids:
                row = incidents[incident_id]
                await self.broadcast(
                    {"type": "incident", "data": record_to_incident(row).model_dump()}
                )
            await self.broadcast(
                {
                    "type": "resources",
                    "data": [item.model_dump() for item in self.manager.resources.values()],
                }
            )
            if timeline_changed:
                await self.broadcast({"type": "timeline", "data": list(self.timeline)})
            snapshot = self.snapshot()
            await self.broadcast({"type": "stats", "data": snapshot["stats"]})
            return any(
                item.status in {ResourceStatus.EN_ROUTE, ResourceStatus.ON_SCENE}
                for item in self.manager.resources.values()
            )
        finally:
            db.close()

    def _ensure_lifecycle_task(self) -> None:
        if self.lifecycle_task and not self.lifecycle_task.done():
            return
        self.lifecycle_task = asyncio.create_task(self._run_lifecycle_until_idle())

    async def _run_lifecycle_until_idle(self) -> None:
        try:
            for _ in range(500):
                async with self._lock:
                    active = await self._tick_resources()
                if not active:
                    break
                await asyncio.sleep(max(self.settings.SIMULATION_DELAY_SECONDS, 0.05))
        except asyncio.CancelledError:
            return

    async def _cancel_background_tasks(self) -> None:
        current = asyncio.current_task()
        tasks = [
            task
            for task in (self.task, self.lifecycle_task)
            if task and not task.done() and task is not current
        ]
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self.task = None
        self.lifecycle_task = None

    def _record_event(
        self,
        event_type: str,
        title: str,
        detail: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._event_counter += 1
        self.timeline.append(
            {
                "id": f"event-{self._event_counter}",
                "timestamp": datetime.now().isoformat(),
                "type": event_type,
                "title": title,
                "detail": detail,
                "metadata": metadata or {},
            }
        )
        self.timeline = self.timeline[-80:]

    def _scenario_payload(self) -> dict[str, Any]:
        scenario = SCENARIOS[self.scenario]
        return {
            "id": scenario["id"],
            "label": scenario["label"],
            "description": scenario["description"],
            "focus": scenario["focus"],
            "default_calls": scenario["default_calls"],
        }

    def _after_action_report(
        self,
        stats: dict[str, Any],
        incidents: list[IncidentResponse],
    ) -> dict[str, Any]:
        end = self.completed_at or datetime.now()
        duration = (end - self.started_at).total_seconds() if self.started_at else 0
        unique = len(incidents)
        duplicates = max(self.incoming_reports - unique, 0)
        resolved = sum(1 for incident in incidents if incident.status == "Resolved")
        approvals = sum(1 for incident in incidents if incident.dispatcher_approved)
        reduction = round((duplicates / self.incoming_reports) * 100) if self.incoming_reports else 0
        return {
            "scenario": self._scenario_payload(),
            "state": self.state,
            "generated_at": datetime.now().isoformat(),
            "duration_seconds": round(duration, 1),
            "metrics": {
                "incoming_reports": self.incoming_reports,
                "unique_incidents": unique,
                "duplicates_consolidated": duplicates,
                "noise_reduction_percent": reduction,
                "critical_incidents": stats.get("critical_incidents", 0),
                "dispatcher_approvals": approvals,
                "resolved_incidents": resolved,
                "peak_utilization_percent": round(self.peak_utilization * 100),
                "average_confidence_percent": round(stats.get("average_confidence", 0) * 100),
            },
            "highlights": [
                f"Consolidated {duplicates} duplicate reports into a shared operational picture.",
                f"Identified {stats.get('critical_incidents', 0)} P1 incidents for immediate review.",
                f"Recorded {approvals} human-approved dispatch decision{'s' if approvals != 1 else ''}.",
                f"Resolved {resolved} incident{'s' if resolved != 1 else ''} during the session.",
            ],
            "recommendations": [
                "Review unassigned P1 incidents before standing down surge staffing.",
                "Preserve coverage near the highest predicted-demand zone.",
                "Export the decision log for dispatcher debrief and model review.",
            ],
        }

    def _reset_db(self) -> None:
        db = SessionLocal()
        try:
            clear_operational_data(db)
            seed_operational_data(db)
            db.commit()
        finally:
            db.close()

    def _upsert_incident(self, db: Session, incident: IncidentResponse) -> None:
        db.merge(Incident(**incident_to_record(incident)))

    def _upsert_resource(self, db: Session, resource: ResourceResponse) -> None:
        db.merge(
            Resource(
                id=resource.id,
                type=resource.type.value,
                lat=resource.location.lat,
                lng=resource.location.lng,
                status=resource.status.value,
                speed_mph=resource.speed_mph,
                station=resource.station,
                current_incident_id=resource.current_incident_id,
                eta=resource.eta,
            )
        )

    def _resource_schema(self, row: Resource) -> ResourceResponse:
        return ResourceResponse(
            id=row.id,
            type=ResourceType(row.type),
            location=Location(lat=row.lat, lng=row.lng),
            speed_mph=row.speed_mph,
            status=ResourceStatus(row.status),
            current_incident_id=row.current_incident_id,
            station=row.station,
            eta=row.eta,
        )

    def _hospital_schema(self, row: Hospital) -> HospitalResponse:
        return HospitalResponse(
            id=row.id,
            name=row.name,
            location=Location(lat=row.lat, lng=row.lng),
            capacity=row.capacity,
            occupancy=row.occupancy,
            available_beds=max(row.capacity - row.occupancy, 0),
        )

    async def _send(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        await websocket.send_json(message)


simulation = SimulationEngine()
