from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database.session import Base


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    incident_type: Mapped[str] = mapped_column(String(32), nullable=False)
    severity: Mapped[str] = mapped_column(String(8), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    clustered_calls: Mapped[str] = mapped_column(Text, default="[]")
    assigned_resource: Mapped[str] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="Pending")
    context: Mapped[str] = mapped_column(Text, default="{}")
    recommended_response: Mapped[str] = mapped_column(Text, nullable=True)
    dispatcher_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    call_count: Mapped[int] = mapped_column(Integer, default=1)
