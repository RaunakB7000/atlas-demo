from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database.session import Base


class Hospital(Base):
    __tablename__ = "hospitals"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, default=20)
    occupancy: Mapped[int] = mapped_column(Integer, default=8)
