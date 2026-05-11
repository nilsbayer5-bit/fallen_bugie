from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ScanJob(Base):
    __tablename__ = "scanjobs"

    id = Column(Integer, primary_key=True, index=True)
    target = Column(String, nullable=False)
    scan_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="queued")
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
