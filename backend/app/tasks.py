from .celery_app import celery
from . import scanner, database, models
from sqlalchemy.orm import Session
import logging
import subprocess
import json
import re
import shutil
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
            # Probe nuclei binary and choose JSON vs human-readable mode accordingly.
            try:
                which_nuclei = shutil.which("nuclei")
                logger.info("nuclei path: %s", which_nuclei)
            except Exception:
                which_nuclei = None

            help_text = ""
            try:
                help_proc = subprocess.run(["nuclei", "-h"], capture_output=True, text=True, timeout=10)
                help_text = (help_proc.stdout or "") + (help_proc.stderr or "")
                logger.debug("nuclei help length=%d", len(help_text))
            except Exception:
                logger.debug("nuclei help probe failed")

            try:
                help_lower = (help_text or "").lower()
                json_flag = None
                if help_lower:
                    if re.search(r'(^|\s)-json(\s|,|$)', help_lower):
                        json_flag = '-json'
                    elif re.search(r'(^|\s)-jsonl(\s|,|$)', help_lower) or re.search(r'(^|\s)-j(\s|,|$)', help_lower):
                        json_flag = '-jsonl'

                if json_flag == '-json':
                    proc = subprocess.run(["nuclei", "-u", scan.target, "-json"], capture_output=True, text=True, timeout=300)
                elif json_flag == '-jsonl':
                    proc = subprocess.run(["nuclei", "-u", scan.target, "-jsonl"], capture_output=True, text=True, timeout=300)
                else:
                    logger.info("nuclei: no JSON output flag found; running human-readable mode")
                    proc = subprocess.run(["nuclei", "-u", scan.target], capture_output=True, text=True, timeout=600)

                out = proc.stdout or ""
                err = proc.stderr or ""
                rc = proc.returncode
                logger.info("nuclei rc=%s stdout_len=%d stderr_len=%d", rc, len(out), len(err))
                if rc != 0:
                    logger.warning("nuclei non-zero exit (rc=%s). stdout_len=%d stderr_len=%d", rc, len(out), len(err))
                    if out:
                        logger.warning("nuclei stdout (truncated): %s", out[:1000])
                    if err:
                        logger.warning("nuclei stderr (truncated): %s", err[:1000])
                elif err:
                    logger.warning("nuclei stderr present (rc=%s): %s", rc, err[:1000])

                # Try JSON-lines parsing first
                findings = []
                json_parse_ok = True
                for line in out.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        findings.append(json.loads(line))
                    except Exception:
                        json_parse_ok = False
                        findings = []
                        break

                if json_parse_ok and findings:
                    results["nuclei"] = findings
                else:
                    # human-readable parsing: strip ANSI and parse per-line findings
                    ansi_re = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
                    pattern = re.compile(r'^\[(?P<template>[^\]]+)\]\s+\[(?P<proto>[^\]]+)\]\s+\[(?P<severity>[^\]]+)\]\s+(?P<target>.+)$')
                    findings2 = []
                    for l in out.splitlines():
                        clean_line = ansi_re.sub('', l).strip()
                        if not clean_line:
                            continue
                        m = pattern.match(clean_line)
                        if m:
                            findings2.append({
                                "template": m.group('template'),
                                "proto": m.group('proto'),
                                "severity": m.group('severity'),
                                "target": m.group('target'),
                                "raw": clean_line,
                            })

                    if findings2:
                        results["nuclei"] = findings2
                    else:
                        out_clean = "\n".join([ansi_re.sub('', ln) for ln in out.splitlines()])
                        m_total = re.search(r'Scan completed in .*? (?P<matches>\d+) matches found', out_clean)
                        if m_total:
                            matches = int(m_total.group('matches'))
                            if matches == 0:
                                results["nuclei"] = []
                            else:
                                results["nuclei"] = {"note": f"nuclei found {matches} matches (unparsed)", "matches": matches, "stdout": out_clean, "stderr": err, "returncode": rc}
                        else:
                            results["nuclei"] = {"note": "nuclei ran but no parseable findings", "stdout": out_clean, "stderr": err, "returncode": rc}
            except FileNotFoundError:
                results["nuclei"] = {"error": "nuclei binary not found"}
            except subprocess.TimeoutExpired:
                results["nuclei"] = {"error": "nuclei timed out"}

        # placeholders for other tools
        if "subfinder" in tools_to_run:
            results["subfinder"] = {"note": "not implemented in prototype"}
        if "katana" in tools_to_run:
            results["katana"] = {"note": "not implemented in prototype"}

        # compute overall risk and collect human-readable reasons
        def map_severity(s):
            if not s or not isinstance(s, str):
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
        reasons = []

        # check nuclei findings (handle list or dict error blobs)
        nuclei_findings = results.get("nuclei")
        if isinstance(nuclei_findings, dict):
            # possible shapes: {error:..., returncode:..., stderr:..., stdout:...} or {findings: [...], stderr: ...}
            if nuclei_findings.get("error"):
                rc = nuclei_findings.get("returncode")
                msg = nuclei_findings.get("stderr") or nuclei_findings.get("stdout") or ""
                reasons.append(f"nuclei error: {nuclei_findings.get('error')} (rc={rc}) {msg}".strip())
            elif nuclei_findings.get("findings") is not None:
                nuclei_list = nuclei_findings.get("findings")
                if isinstance(nuclei_list, list):
                    nuclei_findings = nuclei_list
                else:
                    nuclei_findings = []

        if isinstance(nuclei_findings, list):
            for f in nuclei_findings:
                sev = None
                name = None
                if isinstance(f, dict):
                    if isinstance(f.get("severity"), str):
                        sev = f.get("severity")
                    else:
                        info = f.get("info")
                        if isinstance(info, dict):
                            sev = info.get("severity") or info.get("level") or None
                            name = info.get("name") or info.get("title") or None
                    name = name or f.get("template") or f.get("name") or f.get("id")
                mapped = map_severity(sev)
                if mapped == "Critical":
                    highest = "Critical"
                    reasons.append(f"Nuclei: {name or 'finding'} severity {mapped}")
                    break
                if mapped == "High" and highest not in ("Critical", "High"):
                    highest = "High"
                    reasons.append(f"Nuclei: {name or 'finding'} severity {mapped}")
                if mapped == "Medium" and highest not in ("Critical", "High", "Medium"):
                    highest = "Medium"
                    reasons.append(f"Nuclei: {name or 'finding'} severity {mapped}")
                if mapped == "Low" and highest == "Safe":
                    highest = "Low"
                    reasons.append(f"Nuclei: {name or 'finding'} severity {mapped}")

        # check nmap heuristic
        nmap_res = results.get("nmap")
        try:
            for h in (nmap_res or {}).get("hosts", []):
                host_label = h.get("host") or h.get("ip") or 'host'
                for p in h.get("ports", []):
                    if p.get("port") == 22 and p.get("state") == "open":
                        if highest != "Critical":
                            highest = "High"
                            reasons.append(f"Nmap: {host_label} port 22 open (High)")
                    if p.get("port") in (80, 443) and p.get("state") == "open":
                        if highest not in ("Critical", "High", "Medium"):
                            highest = "Medium"
                            reasons.append(f"Nmap: {host_label} port {p.get('port')} open (Medium)")
        except Exception:
            logger.exception("nmap heuristic failed")

        # finalise reason text
        if not reasons:
            reasons.append("No findings detected")

        scan.result = results
        scan.overall_risk = highest
        scan.risk_explanation = "; ".join(reasons)
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
