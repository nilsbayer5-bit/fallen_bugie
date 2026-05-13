from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class ScanRequest(BaseModel):
    target: str
    scan_type: str  # network or web
    scan_mode: Optional[str] = "Full Scan"
    selected_tools: Optional[List[str]] = None
    is_scheduled: Optional[bool] = False
    cron_schedule: Optional[str] = None

    model_config = {"from_attributes": True}


class ScanResponse(BaseModel):
    id: int
    target: str
    scan_type: str
    scan_mode: Optional[str]
    selected_tools: Optional[List[str]]
    status: str
    celery_id: Optional[str]
    is_scheduled: Optional[bool]
    cron_schedule: Optional[str]
    overall_risk: Optional[str]
    risk_explanation: Optional[str]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ScanListItem(BaseModel):
    id: int
    target: str
    scan_type: str
    scan_mode: Optional[str]
    status: str
    overall_risk: Optional[str]
    risk_explanation: Optional[str]
    is_scheduled: Optional[bool]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ScanDetail(BaseModel):
    id: int
    target: str
    scan_type: str
    scan_mode: Optional[str]
    selected_tools: Optional[List[str]]
    status: str
    result: Optional[Any]
    overall_risk: Optional[str]
    risk_explanation: Optional[str]
    is_scheduled: Optional[bool]
    cron_schedule: Optional[str]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}
