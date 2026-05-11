from celery import Celery
import os

# Simple Celery factory using Redis. Configure with env vars if needed.
REDIS_URL = os.getenv("FALLEN_BUDGIE_REDIS", "redis://localhost:6379/0")

celery = Celery(
    "fallen_budgie",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["backend.app.tasks", "app.tasks"],
)

# Optional: keep celery config here
celery.conf.task_routes = {"app.tasks.*": {"queue": "scans"}}
