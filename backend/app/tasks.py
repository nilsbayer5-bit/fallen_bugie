from .celery_app import celery
from . import scanner, database, models
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


@celery.task(name="app.tasks.scan_task")
def scan_task(scan_id: int):
    """Celery task that loads the scan record, runs an nmap scan and stores the result.

    For now this implements only a network nmap scan. Web scanning via nuclei can be added
    by invoking the nuclei binary via subprocess from here.
    """
    db: Session = database.SessionLocal()
    scan = db.query(models.ScanJob).filter(models.ScanJob.id == scan_id).first()
    if not scan:
        logger.error("Scan id %s not found", scan_id)
        return {"error": "scan not found"}

    try:
        scan.status = "running"
        db.add(scan)
        db.commit()

        if scan.scan_type == "network":
            result = scanner.run_nmap_scan(scan.target)
        else:
            # placeholder for web scans (nuclei)
            result = {"error": "web scan not implemented yet"}

        scan.result = result
        scan.status = "done"
        db.add(scan)
        db.commit()
        return {"ok": True, "scan_id": scan_id}
    except Exception as e:
        logger.exception("scan task failed")
        scan.status = "error"
        scan.result = {"error": str(e)}
        db.add(scan)
        db.commit()
        return {"ok": False, "error": str(e)}
