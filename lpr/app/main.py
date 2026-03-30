from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from .database import Base, engine, get_db
from .models import Stage, Vehicle, DriveThruVisit
from .schemas import IngestResponse, LoyaltyLinkIn, MetricsOut, VehicleOut, VisitOut
from .services.metrics import MetricsService
from .services.tracking import TrackingService
from .services.vision import CarVisionService

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Drive-Thru LPR Service", version="0.1.0")
vision_service = CarVisionService()
images_dir = Path("data/images")
images_dir.mkdir(parents=True, exist_ok=True)


def parse_stage(stage: str) -> Stage:
    try:
        return Stage(stage.lower())
    except ValueError as exc:
        allowed = ", ".join(s.value for s in Stage)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stage '{stage}'. Use one of: {allowed}",
        ) from exc


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/events/upload", response_model=IngestResponse)
async def upload_event(
    stage: str = Form("entry"),
    camera_id: str = Form("unknown"),
    event_time: datetime | None = Form(None),
    image: UploadFile | None = File(None),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    upload = image or file
    if upload is None:
        raise HTTPException(status_code=400, detail="Upload file in form field 'image' or 'file'")

    parsed_stage = parse_stage(stage)
    raw = await upload.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Image is empty")

    try:
        analysis = vision_service.analyze(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    tracking = TrackingService(db)
    vehicle = tracking.resolve_vehicle(analysis.plate_text, analysis.signature)

    ts = event_time or datetime.utcnow()
    visit = tracking.resolve_visit(vehicle.id, parsed_stage, ts)

    ext = Path(upload.filename or "img.jpg").suffix or ".jpg"
    image_name = f"{uuid4().hex}{ext}"
    image_path = images_dir / image_name
    image_path.write_bytes(raw)

    stage_event = tracking.create_stage_event(
        visit_id=visit.id,
        stage=parsed_stage,
        event_time=ts,
        camera_id=camera_id,
        image_path=str(image_path),
        plate_text=analysis.plate_text,
        plate_confidence=analysis.plate_confidence,
        signature=analysis.signature,
    )

    db.commit()

    return IngestResponse(
        vehicle_id=vehicle.id,
        visit_id=visit.id,
        stage_event_id=stage_event.id,
        plate_text=analysis.plate_text,
        plate_confidence=analysis.plate_confidence,
    )


@app.post("/loyalty/link", response_model=VehicleOut)
def link_loyalty(payload: LoyaltyLinkIn, db: Session = Depends(get_db)):
    vehicle: Vehicle | None = None

    if payload.vehicle_id:
        vehicle = db.get(Vehicle, payload.vehicle_id)
    elif payload.plate_text:
        normalized = payload.plate_text.upper().replace(" ", "")
        vehicle = db.scalar(select(Vehicle).where(Vehicle.canonical_plate == normalized))

    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    vehicle.loyalty_guest_id = payload.guest_id
    db.commit()
    db.refresh(vehicle)
    return vehicle


@app.get("/vehicles/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = db.get(Vehicle, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@app.get("/visits/{visit_id}", response_model=VisitOut)
def get_visit(visit_id: int, db: Session = Depends(get_db)):
    visit = db.scalar(
        select(DriveThruVisit)
        .options(joinedload(DriveThruVisit.stage_events))
        .where(DriveThruVisit.id == visit_id)
    )
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    return visit


@app.get("/metrics/summary", response_model=MetricsOut)
def get_metrics(
    start: datetime | None = None,
    end: datetime | None = None,
    db: Session = Depends(get_db),
):
    return MetricsService(db).summary(start=start, end=end)
