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


# Ensure compatibility with Pydantic v2 `from_orm` behavior by enabling
# `from_attributes=True` on models when supported. This lets `from_orm()`
# work with SQLAlchemy model instances without raising the PydanticUserError.
if hasattr(BaseModel, "model_config"):
    for _cls in (ScanRequest, ScanResponse, ScanListItem, ScanDetail):
        _existing = getattr(_cls, "model_config", None)
        if isinstance(_existing, dict):
            new = dict(_existing)
            new["from_attributes"] = True
            _cls.model_config = new
        else:
            _cls.model_config = {"from_attributes": True}
