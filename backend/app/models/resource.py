from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database.session import Base


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="Available")
    speed_mph: Mapped[int] = mapped_column(Integer, default=40)
    station: Mapped[str] = mapped_column(String(64), nullable=False)
    current_incident_id: Mapped[str] = mapped_column(String(64), nullable=True)
    eta: Mapped[float] = mapped_column(Float, nullable=True)
