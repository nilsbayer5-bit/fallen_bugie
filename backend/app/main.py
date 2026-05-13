from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os

from . import database, models, schemas, tasks

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="fallen_budgie API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/scan", response_model=schemas.ScanResponse)
def create_scan(req: schemas.ScanRequest):
    """Enqueue a scan job. Returns the DB record and Celery task id.

    scan_type: "network" or "web"
    target: IP address or URL
    """
    db: Session = database.SessionLocal()
    scan = models.ScanJob(target=req.target, scan_type=req.scan_type, status="queued")
    db.add(scan)
    db.commit()
    db.refresh(scan)

    # enqueue the celery task and pass the scan id
    task = tasks.scan_task.delay(scan.id)

    return {
        "id": scan.id,
        "target": scan.target,
        "scan_type": scan.scan_type,
        "status": scan.status,
        "celery_id": task.id,
    }


@app.get("/scans", response_model=list[schemas.ScanListItem])
def list_scans():
    db: Session = database.SessionLocal()
    rows = db.query(models.ScanJob).order_by(models.ScanJob.created_at.desc()).all()
    # Convert SQLAlchemy models to plain dicts so Pydantic v2 validation works
    result = []
    for r in rows:
        result.append({
            "id": r.id,
            "target": r.target,
            "scan_type": r.scan_type,
            "status": r.status,
            "created_at": r.created_at,
        })
    return result


@app.get("/scans/{scan_id}", response_model=schemas.ScanDetail)
def get_scan(scan_id: int):
    db: Session = database.SessionLocal()
    scan = db.query(models.ScanJob).filter(models.ScanJob.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return {
        "id": scan.id,
        "target": scan.target,
        "scan_type": scan.scan_type,
        "status": scan.status,
        "result": scan.result,
        "created_at": scan.created_at,
    }
