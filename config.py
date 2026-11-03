"""Central place for every runtime setting. Nothing here is hardcoded for a
specific environment: each value comes from an environment variable with a
safe local-development default."""
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Celery can use separate URLs, but by default both broker and result
# backend point at the same Redis instance.
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

# How long the demo task "works" for, so the frontend has something to poll.
TASK_DELAY_SECONDS = float(os.getenv("TASK_DELAY_SECONDS", "5"))
RESULT_EXPIRES_SECONDS = int(os.getenv("RESULT_EXPIRES_SECONDS", "3600"))

# Comma separated list of allowed origins. Only needed when the frontend is
# served from a different origin than the API (e.g. opening index.html as a file).
CORS_ORIGINS = [
    o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()
]

# When set, the API also serves the static frontend from this directory.
FRONTEND_DIR = os.getenv("FRONTEND_DIR", "")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
