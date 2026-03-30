# Drive-Thru Vehicle Tracking + License Plate Reading (OSS)

This backend ingests car images from drive-thru cameras, extracts license plates using open-source tooling, and tracks each vehicle through stages (`entry`, `menu`, `pickup`, `exit`).

It solves:
1. Unique-ish car identification + timing metrics by stage.
2. Loyalty linking by assigning a guest ID to a resolved vehicle.

## Stack (No paid APIs)
- FastAPI for HTTP service
- OpenCV + Haar cascade for plate candidate detection
- EasyOCR for OCR
- SQLite + SQLAlchemy for storage

## Run
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API

### 1) Ingest drive-thru event with image
```bash
curl -X POST http://127.0.0.1:8000/events/upload \
  -F "stage=entry" \
  -F "camera_id=cam-entry-1" \
  -F "event_time=2026-02-26T18:22:00" \
  -F "image=@/absolute/path/to/car.jpg"
```

### 2) Link vehicle to loyalty guest
```bash
curl -X POST http://127.0.0.1:8000/loyalty/link \
  -H "Content-Type: application/json" \
  -d '{"vehicle_id": 1, "guest_id": "guest_123"}'
```

### 3) Query visit metrics
```bash
curl "http://127.0.0.1:8000/metrics/summary"
```

## Notes
- Plate-first identity: if plate is recognized, that is the primary key for matching.
- Fallback identity: if plate cannot be read, a visual signature (HSV histogram) is used for short-term matching.
- Images are stored in `data/images` and DB in `data/drive_thru.db`.

## Production hardening you should add next
- Multi-camera calibration and per-lane visit stitching
- Better ALPR detector (e.g., YOLO plate detector) for higher recall
- Confidence thresholds + human-review queue for low-confidence plate reads
- Async queue (Kafka/RabbitMQ) for high throughput
- Retention/privacy policy for images and plate data
