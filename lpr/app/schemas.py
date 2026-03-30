from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .models import Stage


class StageEventOut(BaseModel):
    id: int
    stage: Stage
    event_time: datetime
    camera_id: str
    plate_text: str | None
    plate_confidence: float | None

    model_config = ConfigDict(from_attributes=True)


class VisitOut(BaseModel):
    id: int
    vehicle_id: int
    started_at: datetime
    exited_at: datetime | None
    stage_events: list[StageEventOut] = []

    model_config = ConfigDict(from_attributes=True)


class VehicleOut(BaseModel):
    id: int
    canonical_plate: str | None
    loyalty_guest_id: str | None

    model_config = ConfigDict(from_attributes=True)


class IngestResponse(BaseModel):
    vehicle_id: int
    visit_id: int
    stage_event_id: int
    plate_text: str | None
    plate_confidence: float | None


class LoyaltyLinkIn(BaseModel):
    guest_id: str
    vehicle_id: int | None = None
    plate_text: str | None = None


class MetricsOut(BaseModel):
    total_visits: int
    completed_visits: int
    avg_total_seconds: float | None
    avg_entry_to_menu_seconds: float | None
    avg_menu_to_pickup_seconds: float | None
    avg_pickup_to_exit_seconds: float | None
