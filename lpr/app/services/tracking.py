import json
from datetime import datetime, timedelta

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import DriveThruVisit, Stage, StageEvent, Vehicle


def cosine_similarity(sig1: str, sig2: str) -> float:
    v1 = np.array(json.loads(sig1), dtype=np.float32)
    v2 = np.array(json.loads(sig2), dtype=np.float32)
    denom = float(np.linalg.norm(v1) * np.linalg.norm(v2))
    if denom == 0.0:
        return 0.0
    return float(np.dot(v1, v2) / denom)


class TrackingService:
    def __init__(self, db: Session):
        self.db = db

    def resolve_vehicle(self, plate_text: str | None, signature: str) -> Vehicle:
        if plate_text:
            vehicle = self.db.scalar(select(Vehicle).where(Vehicle.canonical_plate == plate_text))
            if vehicle:
                vehicle.visual_signature = signature
                return vehicle

        recent_vehicles = self.db.scalars(select(Vehicle).where(Vehicle.visual_signature.is_not(None))).all()
        if recent_vehicles:
            best = max(
                ((v, cosine_similarity(signature, v.visual_signature)) for v in recent_vehicles if v.visual_signature),
                key=lambda pair: pair[1],
                default=(None, 0.0),
            )
            if best[0] is not None and best[1] >= 0.95:
                if plate_text and not best[0].canonical_plate:
                    best[0].canonical_plate = plate_text
                best[0].visual_signature = signature
                return best[0]

        vehicle = Vehicle(canonical_plate=plate_text, visual_signature=signature)
        self.db.add(vehicle)
        self.db.flush()
        return vehicle

    def resolve_visit(self, vehicle_id: int, stage: Stage, event_time: datetime) -> DriveThruVisit:
        open_visit = self.db.scalar(
            select(DriveThruVisit)
            .where(DriveThruVisit.vehicle_id == vehicle_id)
            .where(DriveThruVisit.exited_at.is_(None))
            .order_by(DriveThruVisit.started_at.desc())
        )

        if stage == Stage.entry or open_visit is None:
            if open_visit and open_visit.started_at < event_time - timedelta(hours=2):
                open_visit.exited_at = open_visit.started_at + timedelta(hours=2)
            visit = DriveThruVisit(vehicle_id=vehicle_id, started_at=event_time)
            self.db.add(visit)
            self.db.flush()
            return visit

        return open_visit

    def create_stage_event(
        self,
        visit_id: int,
        stage: Stage,
        event_time: datetime,
        camera_id: str,
        image_path: str | None,
        plate_text: str | None,
        plate_confidence: float | None,
        signature: str,
    ) -> StageEvent:
        event = StageEvent(
            visit_id=visit_id,
            stage=stage,
            event_time=event_time,
            camera_id=camera_id,
            image_path=image_path,
            plate_text=plate_text,
            plate_confidence=plate_confidence,
            signature=signature,
        )
        self.db.add(event)

        if stage == Stage.exit:
            visit = self.db.get(DriveThruVisit, visit_id)
            if visit:
                visit.exited_at = event_time

        self.db.flush()
        return event
