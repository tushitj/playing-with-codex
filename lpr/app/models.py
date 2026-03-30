from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Stage(str, Enum):
    entry = "entry"
    menu = "menu"
    pickup = "pickup"
    exit = "exit"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    canonical_plate: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    loyalty_guest_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    visual_signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    visits: Mapped[list["DriveThruVisit"]] = relationship(back_populates="vehicle")


class DriveThruVisit(Base):
    __tablename__ = "drive_thru_visits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    exited_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)

    vehicle: Mapped[Vehicle] = relationship(back_populates="visits")
    stage_events: Mapped[list["StageEvent"]] = relationship(back_populates="visit")


class StageEvent(Base):
    __tablename__ = "stage_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    visit_id: Mapped[int] = mapped_column(ForeignKey("drive_thru_visits.id"), index=True)
    stage: Mapped[Stage] = mapped_column(SqlEnum(Stage), index=True)
    event_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    camera_id: Mapped[str] = mapped_column(String(64), index=True)
    image_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    plate_text: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    plate_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    signature: Mapped[str | None] = mapped_column(Text, nullable=True)

    visit: Mapped[DriveThruVisit] = relationship(back_populates="stage_events")
