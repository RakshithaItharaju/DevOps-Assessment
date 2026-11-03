import logging
import os
from typing import Optional

import redis
from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import config
from worker import celery_app, send_notification

logging.basicConfig(
    level=config.LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("api")

app = FastAPI(title="Notify API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NotifyRequest(BaseModel):
    message: str = Field(default="Hello from the frontend", max_length=500)


@app.post("/notify/", status_code=202)
def notify(payload: Optional[NotifyRequest] = None):
    """Enqueue a background task and return its id immediately."""
    message = payload.message if payload else NotifyRequest().message
    task = send_notification.delay(message)
    logger.info("enqueued task %s", task.id)
    return {"task_id": task.id, "status": "QUEUED"}


@app.get("/task_status/{task_id}")
def task_status(task_id: str):
    """Return the Celery state of a task and, once finished, its result.

    Note: Celery reports PENDING for any id it has never seen, so an unknown
    id looks the same as a task that is still waiting in the queue.
    """
    result = AsyncResult(task_id, app=celery_app)
    body = {"task_id": task_id, "status": result.status}
    if result.successful():
        body["result"] = result.result
    elif result.failed():
        body["error"] = str(result.result)
    return body


@app.get("/health")
def health():
    """Liveness probe used by the load balancer. Does not touch Redis, so a
    Redis outage does not cause the load balancer to kill healthy API tasks."""
    return {"status": "ok"}


@app.get("/ready")
def ready():
    """Readiness probe: verifies the API can reach Redis."""
    try:
        redis.Redis.from_url(config.REDIS_URL, socket_connect_timeout=2).ping()
    except Exception as exc:  # noqa: BLE001
        logger.warning("redis not reachable: %s", exc)
        raise HTTPException(status_code=503, detail="redis unreachable")
    return {"status": "ready"}


# Serve the frontend from the same origin as the API when configured. This
# must be mounted last so it does not shadow the API routes above.
if config.FRONTEND_DIR and os.path.isdir(config.FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=config.FRONTEND_DIR, html=True), name="frontend")
