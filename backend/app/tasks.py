from .celery_app import celery
from . import scanner, database, models
from sqlalchemy.orm import Session
import logging
import subprocess
import json
from datetime import datetime, timedelta
from croniter import croniter

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

        tools_to_run = []
        # Determine tools based on scan_mode and selected_tools
        if scan.scan_mode == "Full Scan":
            tools_to_run = ["nmap", "nuclei"]
        else:
            tools_to_run = (scan.selected_tools or [])

        results = {}

        if "nmap" in tools_to_run or scan.scan_type == "network":
            results["nmap"] = scanner.run_nmap_scan(scan.target)

        if "nuclei" in tools_to_run or scan.scan_type == "web":
            # run nuclei via subprocess and parse JSON lines
            try:
                proc = subprocess.run(["nuclei", "-u", scan.target, "-json"], capture_output=True, text=True, timeout=300)
                out = proc.stdout or ""
                findings = []
                for line in out.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        findings.append(json.loads(line))
                    except Exception:
                        # ignore malformed lines
                        continue
                results["nuclei"] = findings
            except FileNotFoundError:
                results["nuclei"] = {"error": "nuclei binary not found"}
            except subprocess.TimeoutExpired:
                results["nuclei"] = {"error": "nuclei timed out"}

        # placeholders for other tools
        if "subfinder" in tools_to_run:
            results["subfinder"] = {"note": "not implemented in prototype"}
        if "katana" in tools_to_run:
            results["katana"] = {"note": "not implemented in prototype"}

        # compute overall risk
        def map_severity(s):
            if not s:
                return None
            s = s.lower()
            if "critical" in s:
                return "Critical"
            if "high" in s:
                return "High"
            if "medium" in s:
                return "Medium"
            if "low" in s:
                return "Low"
            return None

        highest = "Safe"

        # check nuclei findings
        nuclei_findings = results.get("nuclei")
        if isinstance(nuclei_findings, list):
            for f in nuclei_findings:
                sev = None
                # nuclei typically includes 'info'/'severity' keys
                if isinstance(f, dict):
                    sev = f.get("severity") or f.get("info") or None
                mapped = map_severity(sev)
                if mapped == "Critical":
                    highest = "Critical"
                    break
                if mapped == "High" and highest not in ("Critical", "High"):
                    highest = "High"
                if mapped == "Medium" and highest not in ("Critical", "High", "Medium"):
                    highest = "Medium"
                if mapped == "Low" and highest == "Safe":
                    highest = "Low"

        # check nmap heuristic
        nmap_res = results.get("nmap")
        try:
            for h in (nmap_res or {}).get("hosts", []):
                for p in h.get("ports", []):
                    if p.get("port") == 22 and p.get("state") == "open":
                        if highest != "Critical":
                            highest = "High"
                    if p.get("port") in (80, 443) and p.get("state") == "open":
                        if highest not in ("Critical", "High", "Medium"):
                            highest = "Medium"
        except Exception:
            pass

        scan.result = results
        scan.overall_risk = highest
        scan.status = "done"
        scan.last_run_at = datetime.utcnow()
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



@celery.task(name="app.tasks.dispatch_scheduled_scans")
def dispatch_scheduled_scans():
    """Runs every minute via celery beat. Checks DB for scheduled scans and enqueues them when their cron matches now."""
    db: Session = database.SessionLocal()
    now = datetime.utcnow()
    scans = db.query(models.ScanJob).filter(models.ScanJob.is_scheduled == True, models.ScanJob.cron_schedule != None).all()
    for s in scans:
        try:
            prev = croniter(s.cron_schedule, now).get_prev(datetime)
            # if the previous scheduled time is within the last 70 seconds and we haven't run it yet
            if (now - prev) <= timedelta(seconds=70):
                # avoid duplicate scheduling
                if not s.last_run_at or s.last_run_at < prev:
                    # enqueue
                    celery.send_task("app.tasks.scan_task", args=(s.id,))
                    s.last_run_at = prev
                    db.add(s)
                    db.commit()
        except Exception:
            logger.exception("failed to evaluate schedule for scan %s", s.id)
