from __future__ import annotations

import asyncio
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


TEST_DB = Path(tempfile.gettempdir()) / f"atlas-unittest-{os.getpid()}.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ["AIR_API_KEY"] = ""
os.environ["AIR_API_BASE_URL"] = ""
os.environ["AIR_LLM_MODEL"] = ""
os.environ["AIR_EMBEDDING_MODEL"] = ""
os.environ["AIR_ASR_MODEL"] = ""
os.environ["SIMULATION_BATCH_SIZE"] = "5"
os.environ["SIMULATION_DELAY_SECONDS"] = "0"
os.environ["SIMULATION_ON_SCENE_TICKS"] = "2"

from app.agents.prediction_agent import HOTSPOTS  # noqa: E402
from app.database.session import SessionLocal, engine, init_db  # noqa: E402
from app.models.incident import Incident  # noqa: E402
from app.models.prediction import Prediction  # noqa: E402
from app.models.resource import Resource  # noqa: E402
from app.schemas.incident import (  # noqa: E402
    IncidentResponse,
    IncidentType,
    Location,
    SeverityLevel,
    get_severity_value,
)
from app.schemas.resource import ResourceStatus  # noqa: E402
from app.services.call_processor import (  # noqa: E402
    CallProcessor,
    incident_to_record,
    record_to_incident,
    severity_priority,
)
from app.services.resource_manager import ResourceManager  # noqa: E402
from app.services.simulation_engine import SimulationEngine  # noqa: E402
from app.services.stats_service import StatsService  # noqa: E402
from app.simulator.call_streamer import SCENARIOS, generate_call, seed_simulation  # noqa: E402
from main import app  # noqa: E402


def make_incident(
    incident_id: str,
    severity: SeverityLevel,
    *,
    transcript: str = "Caller reports a traffic collision.",
    lat: float = 33.418,
    lng: float = -111.935,
) -> IncidentResponse:
    return IncidentResponse(
        id=incident_id,
        transcript=transcript,
        incident_type=IncidentType.ACCIDENT,
        severity=severity,
        location=Location(lat=lat, lng=lng),
        timestamp=datetime.now().isoformat(),
        clustered_calls=[int(incident_id.split("_")[-1])],
    )


def make_call(call_id: int, transcript: str, lat: float, lng: float) -> dict:
    return {
        "id": call_id,
        "transcript": transcript,
        "location": {"lat": lat, "lng": lng},
        "timestamp": datetime.now().isoformat(),
        "incident_type": "Medical",
        "raw_audio_url": "",
        "context": {},
    }


class SeverityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        init_db()

    def test_main_imports(self) -> None:
        self.assertEqual(app.title, "Atlas")

    def test_canonical_severity_values(self) -> None:
        self.assertEqual(get_severity_value(SeverityLevel.P1), "P1")
        self.assertEqual(get_severity_value("p2"), "P2")

    def test_allocation_priority_order(self) -> None:
        values = [SeverityLevel.P4, SeverityLevel.P2, SeverityLevel.P1, SeverityLevel.P3]
        ordered = sorted(values, key=severity_priority)
        self.assertEqual(ordered, [SeverityLevel.P1, SeverityLevel.P2, SeverityLevel.P3, SeverityLevel.P4])
        manager = ResourceManager()
        self.assertEqual([manager._severity_priority(item) for item in ordered], [1, 2, 3, 4])

    def test_cluster_escalates_to_p1(self) -> None:
        processor = CallProcessor()
        existing = make_incident("inc_1", SeverityLevel.P3)
        incoming = make_incident(
            "inc_2",
            SeverityLevel.P1,
            transcript="Caller reports an unconscious pedestrian struck by a vehicle.",
        )
        merged = processor.merge_into(existing, incoming)
        self.assertEqual(merged.severity, SeverityLevel.P1)

    def test_unassigned_p1_is_counted(self) -> None:
        result = StatsService.calculate_stats([make_incident("inc_3", SeverityLevel.P1)], [])
        self.assertEqual(result["unassigned_critical"], 1)

    def test_incident_record_stores_plain_severity(self) -> None:
        record = incident_to_record(make_incident("inc_4", SeverityLevel.P1))
        self.assertEqual(record["severity"], "P1")


class SimulationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        init_db()
        self.simulation = SimulationEngine()
        self.simulation._reset_db()
        self.simulation.incoming_reports = 0

    async def asyncTearDown(self) -> None:
        await self.simulation._cancel_background_tasks()

    async def test_reset_seeds_one_prediction_set(self) -> None:
        self.simulation._reset_db()
        db = SessionLocal()
        try:
            self.assertEqual(db.query(Prediction).count(), len(HOTSPOTS))
        finally:
            db.close()

    async def test_recommendation_waits_for_approval_then_resolves(self) -> None:
        await self.simulation._ingest_calls(
            [
                make_call(
                    1001,
                    "Caller reports an unconscious person who is not responding.",
                    33.418,
                    -111.935,
                )
            ],
            allow_replan=False,
        )
        db = SessionLocal()
        try:
            incident = db.query(Incident).filter(Incident.id == "inc_1001").one()
            self.assertIsNone(incident.assigned_resource)
            self.assertEqual(incident.status, "Recommended")
            self.assertFalse(incident.dispatcher_approved)
            self.assertIn("recommended_resource_id", incident.context)
            self.assertIn("recommended_support_units", incident.context)
            self.assertEqual(
                db.query(Resource).filter(Resource.status != ResourceStatus.AVAILABLE.value).count(),
                0,
            )
        finally:
            db.close()

        approved = await self.simulation.approve_incident("inc_1001")
        self.assertTrue(approved["dispatcher_approved"])
        self.assertEqual(approved["status"], "Dispatched")

        self.assertIsNotNone(self.simulation.lifecycle_task)
        await self.simulation.lifecycle_task

        db = SessionLocal()
        try:
            incident = db.query(Incident).filter(Incident.id == "inc_1001").one()
            resource = db.query(Resource).filter(Resource.id == incident.assigned_resource).one()
            self.assertEqual(incident.status, "Resolved")
            self.assertEqual(resource.status, ResourceStatus.AVAILABLE.value)
            self.assertIsNone(resource.current_incident_id)
            self.assertIsNone(resource.eta)
        finally:
            db.close()

    async def test_two_approvals_do_not_share_an_active_resource(self) -> None:
        await self.simulation._ingest_calls(
            [
                make_call(2001, "Unconscious person not responding.", 33.418, -111.935),
                make_call(2002, "Cardiac arrest reported.", 33.440, -111.950),
            ],
            allow_replan=False,
        )
        self.simulation.state = "running"
        await self.simulation.approve_incident("inc_2001")
        await self.simulation.approve_incident("inc_2002")

        db = SessionLocal()
        try:
            active = db.query(Resource).filter(
                Resource.current_incident_id.is_not(None)
            ).all()
            incident_ids = [item.current_incident_id for item in active]
            self.assertEqual(len(incident_ids), len(set(incident_ids)))
            assignments = [
                item.assigned_resource
                for item in db.query(Incident).filter(Incident.status == "Dispatched").all()
            ]
            self.assertEqual(len(assignments), len(set(assignments)))
            for incident in db.query(Incident).filter(Incident.status == "Dispatched").all():
                resource = db.query(Resource).filter(Resource.id == incident.assigned_resource).one()
                self.assertEqual(resource.current_incident_id, incident.id)
        finally:
            db.close()

    async def test_injected_incident_has_at_most_one_active_resource(self) -> None:
        result = await self.simulation.inject_critical()
        incident_id = result["incidents"][0]["id"]

        db = SessionLocal()
        try:
            self.assertEqual(
                db.query(Resource).filter(Resource.current_incident_id == incident_id).count(),
                0,
            )
        finally:
            db.close()

        self.simulation.state = "running"
        await self.simulation.approve_incident(incident_id)
        db = SessionLocal()
        try:
            self.assertLessEqual(
                db.query(Resource).filter(Resource.current_incident_id == incident_id).count(),
                1,
            )
        finally:
            db.close()

    async def test_approved_p1_diversion_is_atomic(self) -> None:
        previous = make_incident("inc_4001", SeverityLevel.P3, lat=33.45, lng=-111.98)
        previous.status = "Dispatched"
        previous.dispatcher_approved = True
        critical = make_incident(
            "inc_4002",
            SeverityLevel.P1,
            transcript="Pedestrian struck and unconscious.",
            lat=33.418,
            lng=-111.935,
        )
        critical.status = "Recommended"

        db = SessionLocal()
        try:
            resources = db.query(Resource).all()
            diverted = resources[0]
            previous.assigned_resource = diverted.id
            diverted.status = ResourceStatus.EN_ROUTE.value
            diverted.current_incident_id = previous.id
            diverted.eta = 10
            for item in resources[1:]:
                item.status = ResourceStatus.UNAVAILABLE.value
                item.current_incident_id = None
                item.eta = None
            db.merge(Incident(**incident_to_record(previous)))
            db.merge(Incident(**incident_to_record(critical)))
            db.commit()
            diverted_id = diverted.id
        finally:
            db.close()

        self.simulation.state = "running"
        approved = await self.simulation.approve_incident(critical.id)
        self.assertEqual(approved["assigned_resource"], diverted_id)

        db = SessionLocal()
        try:
            previous_row = db.query(Incident).filter(Incident.id == previous.id).one()
            critical_row = db.query(Incident).filter(Incident.id == critical.id).one()
            resource = db.query(Resource).filter(Resource.id == diverted_id).one()
            self.assertIsNone(previous_row.assigned_resource)
            self.assertEqual(critical_row.assigned_resource, diverted_id)
            self.assertEqual(resource.current_incident_id, critical.id)
            self.assertEqual(
                db.query(Resource).filter(Resource.current_incident_id == critical.id).count(),
                1,
            )
        finally:
            db.close()

    async def test_reset_cancels_previous_simulation_task(self) -> None:
        await self.simulation.start(num_calls=100, delay=0.05)
        previous = self.simulation.task
        await asyncio.sleep(0)
        await self.simulation.reset()
        self.assertTrue(previous.done())

        await self.simulation.start(num_calls=1, delay=0)
        replacement = self.simulation.task
        self.assertIsNot(previous, replacement)
        await replacement
        self.assertEqual(self.simulation.state, "complete")

    async def test_reset_cancels_lifecycle_task(self) -> None:
        await self.simulation._ingest_calls(
            [make_call(3001, "Unconscious person not responding.", 33.418, -111.935)],
            allow_replan=False,
        )
        await self.simulation.approve_incident("inc_3001")
        lifecycle = self.simulation.lifecycle_task
        self.assertIsNotNone(lifecycle)
        await self.simulation.reset()
        self.assertTrue(lifecycle.done())

    async def test_thirty_call_simulation_completes_without_auto_dispatch(self) -> None:
        await self.simulation.start(num_calls=30, delay=0)
        await self.simulation.task
        self.assertEqual(self.simulation.state, "complete")
        self.assertEqual(self.simulation.incoming_reports, 30)

        db = SessionLocal()
        try:
            self.assertGreater(db.query(Incident).count(), 0)
            self.assertEqual(
                db.query(Resource).filter(Resource.status != ResourceStatus.AVAILABLE.value).count(),
                0,
            )
            self.assertEqual(
                db.query(Incident).filter(Incident.assigned_resource.is_not(None)).count(),
                0,
            )
        finally:
            db.close()

    async def test_recommendation_contains_explainable_factors(self) -> None:
        await self.simulation._ingest_calls(
            [make_call(5001, "Caller reports an unconscious patient who is not responding.", 33.418, -111.935)],
            allow_replan=False,
        )
        db = SessionLocal()
        try:
            incident = record_to_incident(db.query(Incident).filter(Incident.id == "inc_5001").one())
            explanation = incident.context["recommendation_explanation"]
            self.assertGreaterEqual(len(explanation["factors"]), 4)
            self.assertIn("selected_eta", explanation)
            self.assertIn("recommendation_alternatives", incident.context)
        finally:
            db.close()

    async def test_scenario_run_produces_timeline_and_report(self) -> None:
        await self.simulation.start(num_calls=10, delay=0, scenario="monsoon_response")
        await self.simulation.task
        snapshot = self.simulation.snapshot()
        self.assertEqual(snapshot["scenario"]["id"], "monsoon_response")
        self.assertGreaterEqual(len(snapshot["timeline"]), 3)
        self.assertEqual(snapshot["after_action_report"]["metrics"]["incoming_reports"], 10)
        self.assertEqual(snapshot["after_action_report"]["state"], "complete")

    async def test_pause_then_start_resumes_without_reset(self) -> None:
        await self.simulation.start(num_calls=30, delay=0.03, scenario="weekday_commute")
        await asyncio.sleep(0.04)
        await self.simulation.pause()
        paused_count = self.simulation.incoming_reports
        self.assertGreater(paused_count, 0)
        self.assertLess(paused_count, 30)
        await self.simulation.start(delay=0)
        await self.simulation.task
        self.assertEqual(self.simulation.incoming_reports, 30)
        self.assertEqual(self.simulation.state, "complete")

    def test_scenario_inputs_are_deterministic(self) -> None:
        seed = SCENARIOS["asu_game_night"]["seed"]
        seed_simulation(seed)
        first = [generate_call(index, scenario="asu_game_night") for index in range(1, 8)]
        seed_simulation(seed)
        second = [generate_call(index, scenario="asu_game_night") for index in range(1, 8)]
        comparable = lambda calls: [
            (item["transcript"], item["location"], item["incident_type"]) for item in calls
        ]
        self.assertEqual(comparable(first), comparable(second))

    def test_deterministic_scenario_preserves_validated_incident_type(self) -> None:
        processor = CallProcessor()
        call = make_call(
            6001,
            "Caller reports shots fired near an apartment building.",
            33.418,
            -111.935,
        )
        call["incident_type"] = "Disturbance"
        call["deterministic"] = True
        incident = processor.process_call(call)
        self.assertEqual(incident.incident_type, IncidentType.DISTURBANCE)
        self.assertEqual(incident.context["analysis_mode"], "validated scenario replay")


def tearDownModule() -> None:
    engine.dispose()
    TEST_DB.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
