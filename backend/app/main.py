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
    scan = models.ScanJob(
        target=req.target,
        scan_type=req.scan_type,
        scan_mode=req.scan_mode or "Full Scan",
        selected_tools=req.selected_tools,
        is_scheduled=bool(req.is_scheduled),
        cron_schedule=req.cron_schedule,
        status="queued",
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    # enqueue the celery task and pass the scan id
    task = tasks.scan_task.delay(scan.id)

    return {
        "id": scan.id,
        "target": scan.target,
        "scan_type": scan.scan_type,
        "scan_mode": scan.scan_mode,
        "selected_tools": scan.selected_tools,
        "status": scan.status,
        "celery_id": task.id,
        "is_scheduled": scan.is_scheduled,
        "cron_schedule": scan.cron_schedule,
        "overall_risk": scan.overall_risk,
        "risk_explanation": scan.risk_explanation,
        "created_at": scan.created_at,
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
            "scan_mode": r.scan_mode,
            "status": r.status,
            "overall_risk": r.overall_risk,
            "risk_explanation": r.risk_explanation,
            "is_scheduled": r.is_scheduled,
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
        "scan_mode": scan.scan_mode,
        "selected_tools": scan.selected_tools,
        "status": scan.status,
        "result": scan.result,
        "overall_risk": scan.overall_risk,
        "risk_explanation": scan.risk_explanation,
        "is_scheduled": scan.is_scheduled,
        "cron_schedule": scan.cron_schedule,
        "created_at": scan.created_at,
    }



@app.delete("/scans/{scan_id}")
def delete_scan(scan_id: int):
    db: Session = database.SessionLocal()
    scan = db.query(models.ScanJob).filter(models.ScanJob.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    db.delete(scan)
    db.commit()
    return {"ok": True}


@app.get("/scans/{scan_id}/report")
def download_report(scan_id: int):
    from fastapi.responses import StreamingResponse
    import io, json

    db: Session = database.SessionLocal()
    scan = db.query(models.ScanJob).filter(models.ScanJob.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    data = {
        "id": scan.id,
        "target": scan.target,
        "scan_type": scan.scan_type,
        "scan_mode": scan.scan_mode,
        "selected_tools": scan.selected_tools,
        "status": scan.status,
        "overall_risk": scan.overall_risk,
        "risk_explanation": scan.risk_explanation,
        "result": scan.result,
        "created_at": str(scan.created_at),
    }

    buf = io.BytesIO(json.dumps(data, indent=2).encode())
    headers = {"Content-Disposition": f"attachment; filename=scan_{scan_id}_report.json"}
    return StreamingResponse(buf, media_type="application/json", headers=headers)
