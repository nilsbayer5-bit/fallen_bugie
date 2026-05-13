from celery import Celery
import os

# Simple Celery factory using Redis. Configure with env vars if needed.
REDIS_URL = os.getenv("FALLEN_BUDGIE_REDIS", "redis://localhost:6379/0")

celery = Celery(
    "fallen_budgie",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["backend.app.tasks"],
)

# Optional: keep celery config here
celery.conf.task_routes = {"app.tasks.*": {"queue": "scans"}}
# Basic beat schedule: dispatch scheduled scans every minute
from celery.schedules import schedule
celery.conf.beat_schedule = {
    "dispatch_scheduled_scans": {
        "task": "app.tasks.dispatch_scheduled_scans",
        "schedule": 60.0,
    }
}
