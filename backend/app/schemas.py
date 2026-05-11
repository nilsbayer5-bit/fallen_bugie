from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class ScanRequest(BaseModel):
    target: str
    scan_type: str  # network or web


class ScanResponse(BaseModel):
    id: int
    target: str
    scan_type: str
    status: str
    celery_id: Optional[str]


class ScanListItem(BaseModel):
    id: int
    target: str
    scan_type: str
    status: str
    created_at: Optional[datetime]

    class Config:
        orm_mode = True


class ScanDetail(BaseModel):
    id: int
    target: str
    scan_type: str
    status: str
    result: Optional[Any]
    created_at: Optional[datetime]

    class Config:
        orm_mode = True
