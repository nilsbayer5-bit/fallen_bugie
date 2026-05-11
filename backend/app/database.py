from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# SQLite for initial prototype. DB file created in repository root.
DB_URL = os.getenv("FALLEN_BUDGIE_DB", "sqlite:///./fallen_budgie.db")

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
