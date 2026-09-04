from sqlalchemy.orm import Session

from ..agents.prediction_agent import PredictionAgent
from ..models.hospital import Hospital
from ..models.prediction import Prediction
from ..models.resource import Resource
from ..simulator.call_streamer import generate_historical_data
from ..simulator.resource_simulator import HOSPITAL_SEED, generate_resources


def seed_operational_data(db: Session) -> None:
    if db.query(Resource).count() == 0:
        for item in generate_resources():
            db.add(
                Resource(
                    id=item["id"],
                    type=item["type"],
                    lat=item["location"]["lat"],
                    lng=item["location"]["lng"],
                    status=item["status"],
                    speed_mph=item["speed_mph"],
                    station=item["station"],
                    current_incident_id=None,
                    eta=None,
                )
            )

    if db.query(Hospital).count() == 0:
        for item in HOSPITAL_SEED:
            db.add(Hospital(**item))

    if db.query(Prediction).count() == 0:
        for item in PredictionAgent().forecast(generate_historical_data()):
            db.add(
                Prediction(
                    label=item["label"],
                    lat=item["lat"],
                    lng=item["lng"],
                    hour=item["hour"],
                    probability=item["probability"],
                    recommendation=item["recommendation"],
                )
            )

    db.commit()


def clear_operational_data(db: Session) -> None:
    from ..models.call import Call
    from ..models.incident import Incident
    from ..models.prediction import Prediction

    db.query(Call).delete()
    db.query(Incident).delete()
    db.query(Prediction).delete()
    db.query(Resource).delete()
    db.query(Hospital).delete()
    db.commit()
