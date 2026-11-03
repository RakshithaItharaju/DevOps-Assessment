"""End-to-end API tests that need no Redis: Celery runs tasks eagerly and keeps
results in an in-memory backend."""
import os
import pathlib
import sys

# Must be set before the app modules are imported.
os.environ["CELERY_BROKER_URL"] = "memory://"
os.environ["CELERY_RESULT_BACKEND"] = "cache+memory://"
os.environ["TASK_DELAY_SECONDS"] = "0"

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from worker import celery_app  # noqa: E402

celery_app.conf.task_always_eager = True
celery_app.conf.task_store_eager_result = True

client = TestClient(main.app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_notify_then_status_success():
    resp = client.post("/notify/", json={"message": "hi"})
    assert resp.status_code == 202
    task_id = resp.json()["task_id"]
    assert task_id

    status = client.get(f"/task_status/{task_id}").json()
    assert status["status"] == "SUCCESS"
    assert status["result"]["message"] == "hi"
    assert status["result"]["delivered"] is True


def test_notify_without_body_uses_default_message():
    resp = client.post("/notify/")
    assert resp.status_code == 202
    status = client.get(f"/task_status/{resp.json()['task_id']}").json()
    assert status["status"] == "SUCCESS"


def test_notify_rejects_oversized_message():
    resp = client.post("/notify/", json={"message": "x" * 501})
    assert resp.status_code == 422


def test_unknown_task_is_pending():
    status = client.get("/task_status/does-not-exist").json()
    assert status["status"] == "PENDING"
