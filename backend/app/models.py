from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ScanJob(Base):
    __tablename__ = "scanjobs"

    id = Column(Integer, primary_key=True, index=True)
    target = Column(String, nullable=False)
    scan_type = Column(String, nullable=False)
    # New fields
    scan_mode = Column(String, nullable=False, default="Full Scan")
    selected_tools = Column(JSON, nullable=True)
    overall_risk = Column(String, nullable=False, default="Safe")
    is_scheduled = Column(Boolean, nullable=False, default=False)
    cron_schedule = Column(String, nullable=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)

    status = Column(String, nullable=False, default="queued")
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
