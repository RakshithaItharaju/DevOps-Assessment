import logging
import ssl
import time
from datetime import datetime, timezone

from celery import Celery

import config

logging.basicConfig(
    level=config.LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("worker")

celery_app = Celery(
    "worker",
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_track_started=True,  # exposes the STARTED state to the frontend
    result_expires=config.RESULT_EXPIRES_SECONDS,
    broker_connection_retry_on_startup=True,
    worker_prefetch_multiplier=1,
    # If a worker is killed mid-task (e.g. a Fargate deployment), the task is
    # redelivered instead of being lost. Tasks should therefore be idempotent.
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# ElastiCache with in-transit encryption uses rediss:// and needs TLS options.
if config.CELERY_BROKER_URL.startswith("rediss://"):
    celery_app.conf.broker_use_ssl = {"ssl_cert_reqs": ssl.CERT_REQUIRED}
if config.CELERY_RESULT_BACKEND.startswith("rediss://"):
    celery_app.conf.redis_backend_use_ssl = {"ssl_cert_reqs": ssl.CERT_REQUIRED}


@celery_app.task(name="tasks.send_notification", bind=True)
def send_notification(self, message: str) -> dict:
    """Pretend to deliver a notification. Sleeps to simulate real work."""
    logger.info("task %s started: %r", self.request.id, message)
    time.sleep(config.TASK_DELAY_SECONDS)
    result = {
        "message": message,
        "delivered": True,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }
    logger.info("task %s finished", self.request.id)
    return result
