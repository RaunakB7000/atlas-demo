from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database.session import Base


class Call(Base):
    __tablename__ = "calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    incident_type: Mapped[str] = mapped_column(String(32), nullable=True)
    raw_audio_url: Mapped[str] = mapped_column(String(255), nullable=True)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    incident_id: Mapped[str] = mapped_column(String(64), nullable=True)
    context: Mapped[str] = mapped_column(Text, nullable=True)
